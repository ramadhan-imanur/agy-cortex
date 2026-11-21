#!/usr/bin/env python3
"""OpenClaw-style zero-token proactive heartbeat monitor (Windows & Linux).

Runs periodically via Windows Task Scheduler / systemd user timer (0 MB idle).
Performs deterministic local checks (disks, RAM/pagefile, critical services or
scheduler health, and periodic PROGRESS.md sync into hmem) with zero LLM calls.
Logs anomalies locally and emits a desktop notification only outside cooldown.
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import glob
import json
import os
import shutil
import string
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

STATE_FILE = SCRIPTS_DIR / "state/heartbeat_state.json"
ALERT_LOG = SCRIPTS_DIR / "state/heartbeat_alerts.log"
HEARTBEAT_MD = Path(os.environ.get("AGY_HEARTBEAT_MD", "~/.gemini/config/memory/HEARTBEAT.md")).expanduser()
HMEM_SCRIPT = Path(os.environ.get("AGY_HMEM_SCRIPT", "~/.gemini/config/memory/hmem.py")).expanduser()

PROGRESS_SYNC_INTERVAL = 24 * 3600
SYNC_DISK_INTERVAL = 1800

DISK_WARN_PCT = int(os.environ.get("AGY_DISK_WARN_PCT", "90"))
RAM_AVAIL_MIN_MB = int(os.environ.get("AGY_RAM_AVAIL_MIN_MB", "400"))
SWAP_WARN_PCT = int(os.environ.get("AGY_SWAP_WARN_PCT", "85"))
COOLDOWN_SECONDS = int(os.environ.get("AGY_COOLDOWN_HOURS", "4")) * 3600
WIN_TASK_NAME = os.environ.get("AGY_WIN_TASK_NAME", "AntigravityHeartbeat")


def silent_run(cmd: list[str] | str, **kwargs) -> subprocess.CompletedProcess:
    """Run a subprocess silently on Windows without flashing a console window."""
    if os.name == "nt":
        kwargs.setdefault("creationflags", subprocess.CREATE_NO_WINDOW)
    return subprocess.run(cmd, **kwargs)


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def find_external_disk() -> Path | None:
    """Locate portable storage workspace disk across Windows and Linux."""
    env_dir = os.environ.get("HERMES_DISK_MEM_DIR", "").strip()
    if env_dir and Path(env_dir).exists():
        return Path(env_dir)

    if os.name != "nt":
        label = os.environ.get("HERMES_PORTABLE_LABEL", "*")
        for pat in (f"/media/*/{label}", f"/mnt/*/{label}", f"/Volumes/{label}"):
            for match in glob.glob(pat):
                p = Path(match)
                if p.exists() and (p / ".agent").exists():
                    return p
        return None

    for letter in string.ascii_uppercase:
        if letter in ("A", "B", "C"):
            continue
        root = Path(f"{letter}:\\")
        if (root / ".agent").exists():
            return root
    return None


def get_progress_roots(ext_disk: Path | None) -> list[Path]:
    """Return candidate directories containing project PROGRESS.md files."""
    roots: list[Path] = []
    custom = os.environ.get("AGY_PROGRESS_ROOTS", "").strip()
    if custom:
        for p in custom.split(os.pathsep):
            cand = Path(p).expanduser().resolve()
            if cand.exists():
                roots.append(cand)
        return roots

    if ext_disk is not None:
        for subdir in ("Projects", "Workspace"):
            cand = ext_disk / subdir
            if cand.exists():
                roots.append(cand)

    roots.append(Path.home() / "Projects")
    roots.append(Path.home() / "Documents" / "Projects")
    return roots


def get_gpu_summary() -> str | None:
    """Return concise NVIDIA GPU status line if nvidia-smi is available."""
    if not shutil.which("nvidia-smi"):
        return None
    try:
        res = silent_run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=3,
        )
    except Exception:
        return None
    if res.returncode != 0 or not res.stdout.strip():
        return None
    parts = [p.strip() for p in res.stdout.strip().splitlines()[0].split(",")]
    if len(parts) < 4:
        return None
    return f"GPU {parts[0]}: VRAM {parts[1]}/{parts[2]} MiB | Temp {parts[3]} C"


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_alerts": {}, "last_run": 0}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(tmp, STATE_FILE)


def get_mem_stats() -> tuple[int, int]:
    """Return (available_ram_mb, swap_or_commit_pct)."""
    if os.name == "nt":
        stat = _MemoryStatusEx()
        stat.dwLength = ctypes.sizeof(_MemoryStatusEx)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):  # type: ignore[attr-defined]
            return 0, 0
        avail_mb = int(stat.ullAvailPhys // (1024 * 1024))
        total_pf = stat.ullTotalPageFile
        avail_pf = stat.ullAvailPageFile
        commit_pct = int(round(((total_pf - avail_pf) * 100) / total_pf)) if total_pf > 0 else 0
        return avail_mb, commit_pct

    info: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].isdigit():
            info[parts[0].rstrip(":")] = int(parts[1])
    avail_mb = info.get("MemAvailable", 0) // 1024
    swap_total = info.get("SwapTotal", 0)
    swap_free = info.get("SwapFree", 0)
    swap_pct = int(round(((swap_total - swap_free) * 100 / swap_total))) if swap_total > 0 else 0
    return avail_mb, swap_pct


def check_unit(scope: str, unit: str) -> bool:
    cmd = ["systemctl"] + (["--user"] if scope == "user" else []) + ["is-active", "--quiet", unit]
    return silent_run(cmd, capture_output=True).returncode == 0


def get_failed_user_units() -> list[str]:
    res = silent_run(
        ["systemctl", "--user", "--failed", "--no-legend", "--plain"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return [line.split()[0] for line in res.stdout.splitlines() if line.split()]


def check_windows_services(alerts: list[tuple[str, str]], summary: list[str]) -> None:
    """Check optional Windows services and scheduled task health."""
    task_res = silent_run(
        ["schtasks", "/Query", "/TN", WIN_TASK_NAME, "/FO", "LIST"],
        capture_output=True,
        text=True,
    )
    if task_res.returncode == 0:
        disabled = "Disabled" in task_res.stdout
        summary.append(f"Task {WIN_TASK_NAME}: {'DISABLED' if disabled else 'ready'}")
        if disabled:
            alerts.append(("task_heartbeat", f"Scheduled Task inactive: {WIN_TASK_NAME}"))
    else:
        summary.append(f"Task {WIN_TASK_NAME}: NOT REGISTERED")


def run_checks() -> tuple[list[tuple[str, str]], list[str]]:
    alerts: list[tuple[str, str]] = []
    summary: list[str] = []

    ext_disk = find_external_disk()
    disk_targets: list[tuple[str, Path]] = [("home", Path.home())]
    if ext_disk is not None:
        disk_targets.append((f"portable ({ext_disk})", ext_disk))
    else:
        summary.append("Portable disk: not mounted (optional)")

    for label, path in disk_targets:
        if path.exists():
            usage = shutil.disk_usage(path)
            pct = int(round(usage.used * 100 / usage.total))
            free_gb = usage.free / (1024**3)
            summary.append(f"Disk {label}: {pct}% used ({free_gb:.1f} GB free)")
            if pct >= DISK_WARN_PCT:
                alerts.append((f"disk_{label}", f"Disk {label} space low: {pct}% used ({free_gb:.1f} GB free)"))

    avail_mb, swap_pct = get_mem_stats()
    mem_label = "Commit/Pagefile" if os.name == "nt" else "Swap"
    summary.append(f"RAM available: {avail_mb} MB | {mem_label} used: {swap_pct}%")
    if avail_mb < RAM_AVAIL_MIN_MB:
        alerts.append(("ram_low", f"RAM low: {avail_mb} MB available (< {RAM_AVAIL_MIN_MB} MB)"))
    if swap_pct >= SWAP_WARN_PCT:
        alerts.append(("swap_high", f"High {mem_label} usage: {swap_pct}%"))

    if os.name == "nt":
        gpu_line = get_gpu_summary()
        if gpu_line:
            summary.append(gpu_line)
        check_windows_services(alerts, summary)
    else:
        failed = get_failed_user_units()
        if failed:
            summary.append(f"Failed user units: {', '.join(failed)}")
            alerts.append(("failed_units", f"Systemd units failed: {', '.join(failed)}"))
        else:
            summary.append("Failed user units: 0")

    return alerts, summary


def sync_progress_files(state: dict, now_ts: int) -> int:
    """Index changed PROGRESS.md files into hmem once per 24h (0 LLM tokens)."""
    if not HMEM_SCRIPT.exists():
        return 0
    if now_ts - state.get("last_progress_sync", 0) < PROGRESS_SYNC_INTERVAL:
        return 0
    mtimes = state.setdefault("progress_mtimes", {})
    indexed = 0
    py_exe = sys.executable
    for root in get_progress_roots(find_external_disk()):
        if not root.exists():
            continue
        for p in root.rglob("PROGRESS.md"):
            if any(part in (".git", ".Trash-1000", "$RECYCLE.BIN", "node_modules") for part in p.parts):
                continue
            try:
                mt = int(p.stat().st_mtime)
            except OSError:
                continue
            key = str(p)
            if mtimes.get(key) != mt:
                res = silent_run(
                    [py_exe, str(HMEM_SCRIPT), "index-progress", key],
                    capture_output=True,
                    timeout=15,
                )
                if res.returncode == 0:
                    mtimes[key] = mt
                    indexed += 1
    state["last_progress_sync"] = now_ts
    return indexed


def sync_disk_memory(state: dict, now_ts: int) -> bool:
    """Merge local episodic memory & citations with portable storage when mounted."""
    if not HMEM_SCRIPT.exists() or find_external_disk() is None:
        return False
    if now_ts - state.get("last_disk_sync", 0) < SYNC_DISK_INTERVAL:
        return False
    res = silent_run(
        [sys.executable, str(HMEM_SCRIPT), "sync-disk", "--quiet"],
        capture_output=True,
        timeout=30,
    )
    if res.returncode == 0:
        state["last_disk_sync"] = now_ts
        return True
    return False


def emit_local_alert(body: str, now_dt: dt.datetime) -> None:
    """Log alert locally and show a non-blocking desktop notification."""
    ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ALERT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{now_dt.strftime('%Y-%m-%d %H:%M:%S')}] {body}\n")
    print(body, file=sys.stderr)
    if os.name == "nt":
        ps_cmd = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$n = New-Object System.Windows.Forms.NotifyIcon; "
            "$n.Icon = [System.Drawing.SystemIcons]::Warning; "
            "$n.Visible = $true; "
            "$n.ShowBalloonTip(5000, 'Antigravity Heartbeat', $env:AGY_HEARTBEAT_MSG, [System.Windows.Forms.ToolTipIcon]::Warning); "
            "Start-Sleep -Milliseconds 300; $n.Dispose()"
        )
        env = os.environ.copy()
        env["AGY_HEARTBEAT_MSG"] = body[:240]
        silent_run(
            ["powershell.exe", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd],
            env=env,
            capture_output=True,
            timeout=10,
        )
    elif shutil.which("notify-send"):
        silent_run(["notify-send", "Antigravity Heartbeat", body], capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenClaw-style local heartbeat check")
    parser.add_argument("--report", action="store_true", help="Print full status report (even if healthy)")
    parser.add_argument("--dry-run", action="store_true", help="Do not send notifications or persist sync")
    parser.add_argument("--ignore-quiet-hours", action="store_true", help="Run even during night hours")
    args = parser.parse_args()

    now_dt = dt.datetime.now()
    if not args.report and not args.ignore_quiet_hours and not (7 <= now_dt.hour <= 22):
        return 0

    now_ts = int(time.time())
    state = load_state()
    alerts, summary = run_checks()

    if not args.dry_run:
        sync_progress_files(state, now_ts)
        sync_disk_memory(state, now_ts)

    active_alerts: list[str] = []
    last_alerts = state.setdefault("last_alerts", {})
    for key, msg in alerts:
        last_time = last_alerts.get(key, 0)
        if (now_ts - last_time) >= COOLDOWN_SECONDS:
            active_alerts.append(msg)
            last_alerts[key] = now_ts

    if active_alerts and not args.dry_run:
        emit_local_alert("; ".join(active_alerts), now_dt)

    state["last_run"] = now_ts
    if not args.dry_run:
        save_state(state)

    if args.report:
        print("=== Antigravity Heartbeat Report ===")
        print(f"Timestamp: {now_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        for line in summary:
            print(f"- {line}")
        if alerts:
            print("\nAlerts:")
            for _, msg in alerts:
                print(f"  * {msg}")
        else:
            print("\nStatus: OK (no threshold breaches)")

    return 1 if alerts else 0


if __name__ == "__main__":
    raise SystemExit(main())
