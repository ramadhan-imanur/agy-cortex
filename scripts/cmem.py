#!/usr/bin/env python3
"""Cortex Memory Engine: Lightweight persistent memory for Antigravity.

Maintains:
1. Bounded core snapshots (USER.md <= 1500 chars, MEMORY.md <= 2500 chars)
2. Zero-daemon SQLite FTS5 episodic archive (memory.db)
3. Automatic compilation into cortex-memory plugin rules/AGENTS.md
4. Cross-OS bidirectional sync (Windows <-> Linux) via portable storage
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import sqlite3
import string
import sys
from pathlib import Path

BASE_DIR = Path(os.environ.get("CORTEX_MEM_DIR", "~/.gemini/config/memory")).expanduser()
USER_FILE = BASE_DIR / "USER.md"
MEMORY_FILE = BASE_DIR / "MEMORY.md"
DB_FILE = BASE_DIR / "memory.db"
CITATIONS_FILE = BASE_DIR / "citations" / "ledger.json"
PLUGIN_AGENTS_FILE = Path(
    os.environ.get(
        "CORTEX_PLUGIN_AGENTS",
        "~/.gemini/config/plugins/cortex-memory/rules/AGENTS.md",
    )
).expanduser()

LIMITS = {
    "user": 1500,
    "memory": 2500,
}

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    project,
    category,
    title,
    content,
    tags,
    content='entries',
    content_rowid='id',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
    INSERT INTO entries_fts(rowid, project, category, title, content, tags)
    VALUES (new.id, new.project, new.category, new.title, new.content, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, project, category, title, content, tags)
    VALUES ('delete', old.id, old.project, old.category, old.title, old.content, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, project, category, title, content, tags)
    VALUES ('delete', old.id, old.project, old.category, old.title, old.content, old.tags);
    INSERT INTO entries_fts(rowid, project, category, title, content, tags)
    VALUES (new.id, new.project, new.category, new.title, new.content, new.tags);
END;
"""

_DISK_PATH_RE = re.compile(
    r"^(?:[A-Za-z]:[/\\]|/(?:media|mnt)/[^/]+/[^/]+/|/Volumes/[^/]+/)(.+)$"
)


def build_protocol_header() -> str:
    """Build the AGENTS.md protocol header with OS-appropriate CLI invocation."""
    if os.name == "nt":
        cli_hint = f'python "{BASE_DIR / "cmem.py"}"'
    else:
        cli_hint = "python3 ~/.gemini/config/memory/cmem.py"
    return f"""# Cortex Persistent Memory Protocol

You have a lightweight, zero-RAM persistent memory system built natively for Antigravity.
- **Core Memory (Injected Below):** `USER.md` (max 1500 chars) and `MEMORY.md` (max 2500 chars) are already loaded below.
- **Episodic Search (On-Demand):** Do not guess past project history. Search the SQLite FTS5 archive in <5ms when needed:
  `{cli_hint} search "<keywords>"`
- **Save / Supersede Decisions:** After completing a milestone, solving a non-trivial bug, or changing a rule, record it:
  - Detailed/episodic record: `{cli_hint} add --project "<name>" --category "<decision|progress|bugfix|note|convention>" --title "<short title>" --content "<concise details>" [--replace]`
  - Use `--replace` when updating an existing rule/decision so old rules never collide.
  - Core snapshot update (`USER.md` / `MEMORY.md`): update via `{cli_hint} core-set <user|memory> --file <tmp>` (strict char cap enforced; consolidate old entries if near limit).
- **Cross-Device and Workspace Continuity:**
  - Prefer `{cli_hint} search --project "<name>"` and `git status` over creating bloated `PROGRESS.md` changelogs.
  - If an existing `PROGRESS.md` or state doc is updated, overwrite stale rules in place with only the latest compact decisions; run `{cli_hint} sync-disk` after key milestones when portable storage is mounted.
- **Directness:** Match reply length to the weight of the ask with plain claims, clear headings, and concise tables.
"""


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")


def get_conn(db_path: Path = DB_FILE, journal_mode: str = "WAL") -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    sql = (
        SCHEMA_SQL
        if journal_mode.upper() == "WAL"
        else SCHEMA_SQL.replace("PRAGMA journal_mode=WAL;", f"PRAGMA journal_mode={journal_mode};")
    )
    conn.executescript(sql)
    return conn


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def read_core_file(kind: str) -> str:
    target = USER_FILE if kind == "user" else MEMORY_FILE
    if not target.exists():
        return ""
    return target.read_text(encoding="utf-8").strip()


def sync_plugin_rules() -> int:
    user_text = read_core_file("user") or "_(empty)_"
    mem_text = read_core_file("memory") or "_(empty)_"
    compiled = (
        f"{build_protocol_header()}\n"
        f"---\n\n"
        f"## Core Snapshot: USER.md ({len(user_text)}/{LIMITS['user']} chars)\n\n"
        f"{user_text}\n\n"
        f"---\n\n"
        f"## Core Snapshot: MEMORY.md ({len(mem_text)}/{LIMITS['memory']} chars)\n\n"
        f"{mem_text}\n"
    )
    atomic_write(PLUGIN_AGENTS_FILE, compiled)
    return len(compiled)


def safe_fts_query(raw: str, join_or: bool = False) -> str:
    tokens = re.findall(r"[A-Za-z0-9_]+", raw)
    if not tokens:
        return ""
    sep = " OR " if join_or else " "
    return sep.join(f'"{tok}"*' for tok in tokens)


def normalize_disk_relpath(raw_path: str) -> str | None:
    """Convert OS-specific portable disk path to canonical '<portable-disk>/rel/path'."""
    norm = raw_path.strip().replace("\\", "/")
    if norm.startswith("<portable-disk>/"):
        return norm
    m = _DISK_PATH_RE.match(norm)
    if m:
        return f"<portable-disk>/{m.group(1).lstrip('/')}"
    return None


def canonicalize_title(category: str, title: str) -> str:
    if category != "progress-snapshot":
        return title
    m = re.match(r"^PROGRESS\.md snapshot \((.+)\)$", title.strip())
    if not m:
        return title
    canon = normalize_disk_relpath(m.group(1))
    return f"PROGRESS.md snapshot ({canon})" if canon else title


def entry_dedupe_key(project: str, category: str, title: str) -> tuple[str, str, str]:
    return (project, category, canonicalize_title(category, title))


def merge_tags(tags_a: str, tags_b: str) -> str:
    seen: dict[str, None] = {}
    for raw in (tags_a, tags_b):
        for tok in raw.split(","):
            clean = tok.strip()
            if clean:
                seen[clean] = None
    return ",".join(seen.keys())


def find_portable_memory_dir(explicit: str = "") -> Path | None:
    """Locate portable storage memory directory across Windows, Linux, and macOS."""
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("CORTEX_DISK_MEM_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()

    if os.name == "nt":
        for letter in string.ascii_uppercase:
            if letter in ("A", "B", "C"):
                continue
            root = Path(f"{letter}:\\")
            mem_dir = root / ".agent" / "portable-setup" / "memory"
            if (mem_dir / "cmem.py").exists() or (root / ".agent" / "INDEX.json").exists():
                return mem_dir
        return None

    candidates: list[Path] = []
    disk_label = os.environ.get("CORTEX_PORTABLE_LABEL", "*")
    for pat in (
        f"/media/*/{disk_label}/.agent/portable-setup/memory",
        f"/mnt/*/{disk_label}/.agent/portable-setup/memory",
        f"/Volumes/{disk_label}/.agent/portable-setup/memory",
    ):
        candidates.extend(Path(p) for p in glob.glob(pat))
    for cand in candidates:
        if cand.exists():
            return cand
    return None


def cmd_init(_args: argparse.Namespace) -> int:
    conn = get_conn()
    conn.close()
    if not USER_FILE.exists():
        atomic_write(USER_FILE, "# User Profile\n\n- Name: <user>\n")
    if not MEMORY_FILE.exists():
        atomic_write(MEMORY_FILE, "# Core Memory\n\n- Environment initialized.\n")
    size = sync_plugin_rules()
    print(f"Initialized at {BASE_DIR}; compiled AGENTS.md ({size} chars)")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    content = sys.stdin.read().strip() if args.content == "-" else args.content.strip()
    if not content:
        print("Error: content cannot be empty.", file=sys.stderr)
        return 1
    ts = now_iso()
    conn = get_conn()
    action = "Saved"
    row_id = None
    with conn:
        if args.replace:
            existing = conn.execute(
                "SELECT id, tags FROM entries WHERE project = ? AND category = ? AND title = ? ORDER BY id DESC LIMIT 1",
                (args.project, args.category, args.title),
            ).fetchone()
            if existing:
                merged_tags = merge_tags(existing["tags"], args.tags)
                conn.execute(
                    "UPDATE entries SET content = ?, tags = ?, updated_at = ? WHERE id = ?",
                    (content, merged_tags, ts, existing["id"]),
                )
                row_id = existing["id"]
                action = "Updated"
        if row_id is None:
            cur = conn.execute(
                """
                INSERT INTO entries (project, category, title, content, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (args.project, args.category, args.title, content, args.tags, ts, ts),
            )
            row_id = cur.lastrowid
    conn.close()
    print(f"{action} entry #{row_id} [{args.project}/{args.category}] {args.title}")
    return 0


def _run_fts(conn: sqlite3.Connection, fts_q: str, project: str, limit: int) -> list[sqlite3.Row]:
    sql = """
        SELECT e.id, e.project, e.category, e.title, e.content, e.tags, e.updated_at
        FROM entries_fts f
        JOIN entries e ON e.id = f.rowid
        WHERE entries_fts MATCH ?
    """
    params: list[object] = [fts_q]
    if project:
        sql += " AND e.project = ?"
        params.append(project)
    sql += " ORDER BY bm25(entries_fts), e.id DESC LIMIT ?"
    params.append(limit)
    return conn.execute(sql, params).fetchall()


def cmd_search(args: argparse.Namespace) -> int:
    conn = get_conn()
    rows: list[sqlite3.Row] = []
    fts_and = safe_fts_query(args.query, join_or=False)
    if fts_and:
        rows = _run_fts(conn, fts_and, args.project, args.limit)
    if not rows:
        fts_or = safe_fts_query(args.query, join_or=True)
        if fts_or and fts_or != fts_and:
            rows = _run_fts(conn, fts_or, args.project, args.limit)

    if not rows:
        like_pat = f"%{args.query.strip()}%"
        sql = """
            SELECT id, project, category, title, content, tags, updated_at
            FROM entries
            WHERE (title LIKE ? OR content LIKE ? OR project LIKE ? OR tags LIKE ?)
        """
        params = [like_pat, like_pat, like_pat, like_pat]
        if args.project:
            sql += " AND project = ?"
            params.append(args.project)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(args.limit)
        rows = conn.execute(sql, params).fetchall()
    conn.close()

    if not rows:
        print("No matching memories found.")
        return 0
    for r in rows:
        print(f"#{r['id']} [{r['updated_at']}] ({r['project']} | {r['category']}) {r['title']}")
        print(f"  {r['content']}")
        if r["tags"]:
            print(f"  tags: {r['tags']}")
    return 0


def cmd_recent(args: argparse.Namespace) -> int:
    conn = get_conn()
    if args.project:
        rows = conn.execute(
            "SELECT * FROM entries WHERE project = ? ORDER BY id DESC LIMIT ?",
            (args.project, args.limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM entries ORDER BY id DESC LIMIT ?",
            (args.limit,),
        ).fetchall()
    conn.close()
    if not rows:
        print("No episodic entries stored yet.")
        return 0
    for r in rows:
        print(f"#{r['id']} [{r['updated_at']}] ({r['project']} | {r['category']}) {r['title']}")
        print(f"  {r['content']}")
    return 0


def cmd_projects(_args: argparse.Namespace) -> int:
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT project, COUNT(*) AS cnt, MAX(updated_at) AS last_update
        FROM entries
        GROUP BY project
        ORDER BY last_update DESC
        """
    ).fetchall()
    conn.close()
    if not rows:
        print("No projects indexed in episodic memory yet.")
        return 0
    for r in rows:
        print(f"- {r['project']}: {r['cnt']} entries (last: {r['last_update']})")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    conn = get_conn()
    with conn:
        cur = conn.execute("DELETE FROM entries WHERE id = ?", (args.id,))
    conn.close()
    if cur.rowcount == 0:
        print(f"Entry #{args.id} not found.", file=sys.stderr)
        return 1
    print(f"Deleted entry #{args.id}.")
    return 0


def cmd_core_show(_args: argparse.Namespace) -> int:
    for kind, path in (("user", USER_FILE), ("memory", MEMORY_FILE)):
        text = read_core_file(kind)
        print(f"=== {path.name} ({len(text)}/{LIMITS[kind]} chars) ===")
        print(text)
        print()
    return 0


def cmd_core_set(args: argparse.Namespace) -> int:
    if args.file:
        new_text = Path(args.file).expanduser().read_text(encoding="utf-8").strip()
    elif args.content == "-":
        new_text = sys.stdin.read().strip()
    elif args.content is not None:
        new_text = args.content.strip()
    else:
        print("Error: provide --file or --content.", file=sys.stderr)
        return 1

    limit = LIMITS[args.kind]
    if len(new_text) > limit:
        excess = len(new_text) - limit
        print(
            f"Error: {args.kind.upper()}.md limit exceeded ({len(new_text)}/{limit} chars, "
            f"{excess} chars over). Consolidate or prune older lines first.",
            file=sys.stderr,
        )
        return 1

    target = USER_FILE if args.kind == "user" else MEMORY_FILE
    atomic_write(target, new_text + "\n")
    compiled_len = sync_plugin_rules()
    print(
        f"Updated {target.name} ({len(new_text)}/{limit} chars) "
        f"and synced AGENTS.md ({compiled_len} chars)."
    )
    return 0


def cmd_sync(_args: argparse.Namespace) -> int:
    compiled_len = sync_plugin_rules()
    print(f"Synced {PLUGIN_AGENTS_FILE} ({compiled_len} chars).")
    return 0


def cmd_index_progress(args: argparse.Namespace) -> int:
    p = Path(args.path).expanduser().resolve()
    if not p.exists():
        print(f"Error: file not found: {p}", file=sys.stderr)
        return 1
    raw = p.read_text(encoding="utf-8", errors="replace").strip()
    project = args.project or p.parent.name
    compact = raw[:2000] + ("\n...[truncated]" if len(raw) > 2000 else "")
    canon = normalize_disk_relpath(str(p))
    title = f"PROGRESS.md snapshot ({canon or p})"
    ts = now_iso()
    conn = get_conn()
    with conn:
        existing = conn.execute(
            "SELECT id FROM entries WHERE project = ? AND category = 'progress-snapshot' LIMIT 1",
            (project,),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE entries SET title = ?, content = ?, updated_at = ? WHERE id = ?",
                (title, compact, ts, existing["id"]),
            )
            entry_id = existing["id"]
            action = "Updated"
        else:
            cur = conn.execute(
                """
                INSERT INTO entries (project, category, title, content, tags, created_at, updated_at)
                VALUES (?, 'progress-snapshot', ?, ?, 'progress', ?, ?)
                """,
                (project, title, compact, ts, ts),
            )
            entry_id = cur.lastrowid
            action = "Indexed"
    conn.close()
    print(f"{action} #{entry_id} for project '{project}' from {p}")
    return 0


def _read_db_rows(db_path: Path) -> list[dict[str, str]]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT project, category, title, content, tags, created_at, updated_at FROM entries ORDER BY id"
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()
    return [dict(r) for r in rows]


def _read_jsonl_rows(jsonl_path: Path) -> list[dict[str, str]]:
    if not jsonl_path.exists():
        return []
    out: list[dict[str, str]] = []
    for line in jsonl_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if all(k in rec for k in ("project", "category", "title", "content")):
                out.append(rec)
        except json.JSONDecodeError:
            continue
    return out


def _merge_entry_sets(*sources: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[tuple[str, str, str], dict[str, str]] = {}
    for rows in sources:
        for r in rows:
            canon_title = canonicalize_title(r["category"], r["title"])
            key = entry_dedupe_key(r["project"], r["category"], canon_title)
            rec = {
                "project": r["project"],
                "category": r["category"],
                "title": canon_title,
                "content": r["content"],
                "tags": r.get("tags", ""),
                "created_at": r.get("created_at") or r.get("updated_at", ""),
                "updated_at": r.get("updated_at") or r.get("created_at", ""),
            }
            prev = merged.get(key)
            if prev is None:
                merged[key] = rec
                continue
            earliest_created = (
                min(prev["created_at"], rec["created_at"])
                if prev["created_at"] and rec["created_at"]
                else (prev["created_at"] or rec["created_at"])
            )
            combined_tags = merge_tags(prev["tags"], rec["tags"])
            winner = rec if rec["updated_at"] >= prev["updated_at"] else prev
            merged[key] = {
                **winner,
                "tags": combined_tags,
                "created_at": earliest_created,
            }
    return sorted(merged.values(), key=lambda r: (r["created_at"], r["project"], r["category"], r["title"]))


def _write_entries_db(db_path: Path, rows: list[dict[str, str]], journal_mode: str = "WAL") -> None:
    if journal_mode.upper() == "DELETE":
        tmp_db = db_path.with_suffix(".db.tmp")
        if tmp_db.exists():
            tmp_db.unlink()
        conn = get_conn(tmp_db, journal_mode="DELETE")
        with conn:
            conn.executemany(
                "INSERT INTO entries (project, category, title, content, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(r["project"], r["category"], r["title"], r["content"], r["tags"], r["created_at"], r["updated_at"]) for r in rows],
            )
        conn.close()
        os.replace(tmp_db, db_path)
        for suffix in (".db-wal", ".db-shm"):
            stale = db_path.with_suffix(suffix)
            if stale.exists():
                stale.unlink()
        return

    conn = get_conn(db_path, journal_mode=journal_mode)
    with conn:
        conn.execute("DELETE FROM entries")
        conn.executemany(
            "INSERT INTO entries (project, category, title, content, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(r["project"], r["category"], r["title"], r["content"], r["tags"], r["created_at"], r["updated_at"]) for r in rows],
        )
    conn.close()


def _merge_citations(local_path: Path, disk_path: Path) -> int:
    def load_sources(p: Path) -> list[dict]:
        if not p.exists():
            return []
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return data.get("sources", []) if isinstance(data, dict) else []
        except Exception:
            return []

    by_url: dict[str, dict] = {}
    for src in load_sources(disk_path) + load_sources(local_path):
        raw_url = (src.get("url") or "").strip().split("#", 1)[0].rstrip("/")
        if not raw_url:
            continue
        prev = by_url.get(raw_url)
        if prev is None:
            by_url[raw_url] = {
                "url": raw_url,
                "title": src.get("title", ""),
                "accessed": src.get("accessed", ""),
                "quotes": list(src.get("quotes") or []),
            }
            continue
        if not prev["title"] and src.get("title"):
            prev["title"] = src["title"]
        if src.get("accessed", "") > prev.get("accessed", ""):
            prev["accessed"] = src["accessed"]
        seen_q = {q.get("text") for q in prev["quotes"] if isinstance(q, dict)}
        for q in src.get("quotes") or []:
            if isinstance(q, dict) and q.get("text") not in seen_q:
                prev["quotes"].append(q)
                seen_q.add(q.get("text"))

    sources = [{"id": i, **item} for i, item in enumerate(by_url.values(), 1)]
    payload = json.dumps({"version": 1, "sources": sources}, indent=2, ensure_ascii=False) + "\n"
    atomic_write(local_path, payload)
    atomic_write(disk_path, payload)
    return len(sources)


def _sync_shared_user_md(local_user: Path, disk_user: Path) -> bool:
    """Sync newest valid USER.md between local machine and portable storage."""
    l_ok = local_user.exists() and len(local_user.read_text(encoding="utf-8").strip()) > 0
    d_ok = disk_user.exists() and len(disk_user.read_text(encoding="utf-8").strip()) > 0
    if not l_ok and not d_ok:
        return False
    if l_ok and not d_ok:
        txt = local_user.read_text(encoding="utf-8").strip()
        if len(txt) <= LIMITS["user"]:
            atomic_write(disk_user, txt + "\n")
        return False
    if d_ok and not l_ok:
        txt = disk_user.read_text(encoding="utf-8").strip()
        if len(txt) <= LIMITS["user"]:
            atomic_write(local_user, txt + "\n")
            return True
        return False

    l_mtime = local_user.stat().st_mtime
    d_mtime = disk_user.stat().st_mtime
    l_txt = local_user.read_text(encoding="utf-8").strip()
    d_txt = disk_user.read_text(encoding="utf-8").strip()
    if l_txt == d_txt:
        return False
    if d_mtime > l_mtime + 1.0 and len(d_txt) <= LIMITS["user"]:
        atomic_write(local_user, d_txt + "\n")
        return True
    if l_mtime > d_mtime + 1.0 and len(l_txt) <= LIMITS["user"]:
        atomic_write(disk_user, l_txt + "\n")
    return False


def cmd_sync_disk(args: argparse.Namespace) -> int:
    disk_dir = find_portable_memory_dir(args.disk_dir)
    if disk_dir is None or not disk_dir.exists():
        if not args.quiet:
            print("Portable storage directory not found; skipped disk sync.")
        return 0
    if BASE_DIR.resolve() == disk_dir.resolve():
        if not args.quiet:
            print("BASE_DIR already points to portable storage; nothing to merge.")
        return 0

    local_rows = _read_db_rows(DB_FILE)
    disk_jsonl = disk_dir / "episodic_sync.jsonl"
    disk_db = disk_dir / "memory.db"
    disk_rows = _read_jsonl_rows(disk_jsonl) + _read_db_rows(disk_db)

    merged = _merge_entry_sets(disk_rows, local_rows)
    _write_entries_db(DB_FILE, merged, journal_mode="WAL")
    jsonl_text = "\n".join(json.dumps(r, ensure_ascii=False) for r in merged)
    atomic_write(disk_jsonl, (jsonl_text + "\n") if jsonl_text else "")
    _write_entries_db(disk_db, merged, journal_mode="DELETE")

    cit_cnt = _merge_citations(CITATIONS_FILE, disk_dir / "citations" / "ledger.json")
    _sync_shared_user_md(USER_FILE, disk_dir / "USER.md")
    sync_plugin_rules()

    if not args.quiet:
        print(f"Synced with {disk_dir}: {len(merged)} episodic entries, {cit_cnt} citations (MEMORY.md kept machine-local).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cortex Memory CLI for Antigravity")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize DB, core files, and plugin AGENTS.md")

    p_add = sub.add_parser("add", help="Add or replace an episodic memory record")
    p_add.add_argument("--project", required=True, help="Project name or 'global'")
    p_add.add_argument(
        "--category",
        default="note",
        choices=["decision", "progress", "bugfix", "note", "convention"],
    )
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--content", required=True, help="Text or '-' for stdin")
    p_add.add_argument("--tags", default="")
    p_add.add_argument("--replace", action="store_true", help="Replace existing entry with same project/category/title")

    p_search = sub.add_parser("search", help="Full-text search across memories")
    p_search.add_argument("query")
    p_search.add_argument("--project", default="")
    p_search.add_argument("--limit", type=int, default=5)

    p_recent = sub.add_parser("recent", help="Show recent memories")
    p_recent.add_argument("--project", default="")
    p_recent.add_argument("--limit", type=int, default=8)

    sub.add_parser("projects", help="List tracked projects")

    p_del = sub.add_parser("delete", help="Delete memory entry by ID")
    p_del.add_argument("id", type=int)

    sub.add_parser("core-show", help="Show USER.md and MEMORY.md with character counts")

    p_cset = sub.add_parser("core-set", help="Update USER.md or MEMORY.md with strict char limit")
    p_cset.add_argument("kind", choices=["user", "memory"])
    p_cset.add_argument("--file", default="")
    p_cset.add_argument("--content", default=None)

    sub.add_parser("sync", help="Compile USER.md and MEMORY.md into plugin rules/AGENTS.md")

    p_idx = sub.add_parser("index-progress", help="Index a project PROGRESS.md into SQLite FTS5")
    p_idx.add_argument("path")
    p_idx.add_argument("--project", default="")

    p_sd = sub.add_parser("sync-disk", help="Bidirectional merge with portable storage")
    p_sd.add_argument("--disk-dir", default="", help="Override portable storage memory directory")
    p_sd.add_argument("--quiet", action="store_true")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    handlers = {
        "init": cmd_init,
        "add": cmd_add,
        "search": cmd_search,
        "recent": cmd_recent,
        "projects": cmd_projects,
        "delete": cmd_delete,
        "core-show": cmd_core_show,
        "core-set": cmd_core_set,
        "sync": cmd_sync,
        "index-progress": cmd_index_progress,
        "sync-disk": cmd_sync_disk,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
