# OpenClaw-Style Operations Protocol (Portable)

You are equipped with lightweight OpenClaw-style operational layers running with minimal RAM:

- **Proactive Heartbeat (`0 MB` idle):** Scheduled task `AntigravityHeartbeat` (Windows) or `agy-heartbeat.timer` (Linux) runs `heartbeat.py` periodically using deterministic Python checks (`0` LLM tokens), logs/notifies locally only on real anomalies, and automatically runs `hmem.py sync-disk` when portable storage is mounted. Config/checklist lives in `~/.gemini/config/memory/HEARTBEAT.md`.
- **Fair-Use & Safety Guardrail:** Never schedule recurring cron or heartbeat loops that repeatedly call agent/LLM APIs in the background; keep periodic monitoring deterministic in Python/shell.
