---
name: openclaw-ops
description: Manage Antigravity's lightweight OpenClaw-style operations: proactive zero-token heartbeat (HEARTBEAT.md + AntigravityHeartbeat / agy-heartbeat.timer) and automatic cross-OS memory sync. Use when checking system status, configuring heartbeat thresholds, or adding background alerts.
---

# OpenClaw Ops Skill (Portable)

## Components
- **Heartbeat Script:** `scripts/heartbeat.py` (`--report` for full status, `--dry-run` for test)
- **Heartbeat Checklist:** `~/.gemini/config/memory/HEARTBEAT.md`
- **Scheduler Status:**
  - Windows: `schtasks /Query /TN AntigravityHeartbeat /V /FO LIST`
  - Linux: `systemctl --user status agy-heartbeat.timer`

## Rules
1. Keep periodic monitoring deterministic in Python (`0` LLM calls) so token quota and RAM stay untouched.
2. When portable storage is mounted, `heartbeat.py` runs `hmem.py sync-disk --quiet` automatically every 30 minutes (`0` LLM tokens) to keep devices synchronized.
