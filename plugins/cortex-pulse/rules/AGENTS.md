# Cortex Pulse Operations Protocol

You are equipped with a lightweight proactive operational layer running with zero idle RAM:

- **Proactive Pulse (`0 MB` idle):** Scheduled task `CortexPulse` (Windows) or `agy-pulse.timer` (Linux) runs `pulse.py` periodically using deterministic Python checks (`0` LLM tokens), logs or notifies locally only on real anomalies, and runs `cmem.py sync-disk` automatically when portable storage is mounted. Config and checklist live in `~/.gemini/config/memory/PULSE.md`.
- **Fair-Use and Safety Guardrail:** Never schedule recurring cron or heartbeat loops that repeatedly call agent or LLM APIs in the background; keep periodic monitoring deterministic in Python or shell.
