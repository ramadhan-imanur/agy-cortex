# Hermes Memory Engine

Lightweight, zero-RAM persistent memory system modeled after Hermes Agent:

1. **Core Snapshot (`USER.md` & `MEMORY.md`):** Injected automatically into every session via `rules/AGENTS.md` with strict character caps and self-compaction.
2. **Episodic Archive (`memory.db`):** Local SQLite FTS5 database queried in `<5ms` via `hmem.py` without external daemons or heavy vector engines.

## File Locations
- Core data & CLI: `~/.gemini/config/memory/`
- Plugin rules & skills: `~/.gemini/config/plugins/hermes-memory/`
