# Cortex Memory Engine

Lightweight, zero-RAM persistent memory plugin for Antigravity. Architecturally inspired by Hermes-style bounded context snapshots and episodic retrieval, implemented natively in Python and SQLite without third-party daemons.

1. **Core Snapshots (`USER.md` and `MEMORY.md`):** Automatically injected into sessions via `rules/AGENTS.md` with strict character caps.
2. **Episodic Archive (`memory.db`):** Local SQLite FTS5 database queried in under 5 ms via `cmem.py` with no external vector database or background daemon.

## File Locations
- Core data and CLI: `~/.gemini/config/memory/`
- Plugin rules and skills: `~/.gemini/config/plugins/cortex-memory/`
