# Cortex Pulse Monitor

Provides zero-RAM proactive local monitoring for Antigravity without external third-party daemons. Architecturally inspired by heartbeat-driven operational patterns, executed through standard OS schedulers and deterministic Python scripts.

- **Proactive Pulse (0 MB idle):** Scheduled via Windows Task Scheduler (`CortexPulse`) or Linux systemd user timer (`agy-pulse.timer`). Runs `pulse.py` every 30 minutes to check disk usage, available RAM/swap, failed services, and sync workspace progress files without invoking LLM APIs.
- **Checklist:** `~/.gemini/config/memory/PULSE.md`.
