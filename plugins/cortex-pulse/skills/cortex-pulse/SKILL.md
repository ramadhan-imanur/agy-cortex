---
name: cortex-pulse
description: Manage Antigravity's lightweight proactive pulse operations: deterministic zero-token monitoring (PULSE.md + CortexPulse / agy-pulse.timer) and automatic cross-OS memory sync. Use when checking system status, configuring alert thresholds, or reviewing background health logs.
---

# Cortex Pulse Skill

## Components
- **Pulse Monitor Script:** `scripts/pulse.py` (`--report` for full status, `--dry-run` for test)
- **Pulse Checklist:** `~/.gemini/config/memory/PULSE.md`
- **Scheduler Status:**
  - Windows: `schtasks /Query /TN CortexPulse /V /FO LIST`
  - Linux: `systemctl --user status agy-pulse.timer`

## Rules
1. Keep periodic monitoring deterministic in Python (`0` LLM calls) so token quota and RAM stay untouched.
2. When portable storage is mounted, `pulse.py` runs `cmem.py sync-disk --quiet` automatically every 30 minutes (`0` LLM tokens) to keep devices synchronized.
