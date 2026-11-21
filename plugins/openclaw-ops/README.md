# OpenClaw Ops & Heartbeat (Portable)

Provides operational patterns modeled after OpenClaw for Antigravity without heavy node daemons:

- **Heartbeat (0 MB idle):** Scheduled via Windows Task Scheduler (`AntigravityHeartbeat`) or Linux systemd timer (`agy-heartbeat.timer`). Executes `heartbeat.py` every 30 minutes to check disk usage, available RAM/swap, failed units, and sync progress files without making LLM API calls.
- **Checklist:** `~/.gemini/config/memory/HEARTBEAT.md`.
