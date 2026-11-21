# Core Snapshot: Machine and Project Memory (Keep <= 2500 characters)

- Machine and Runtime: Hostname `<HOSTNAME>`, OS `<OS>`, Python `<VERSION>`, key CLIs: `git`, `rg`, `uv`.
- Storage and Workspaces: Local workspace directories (`~/Projects`), portable backup mount points.
- Active Projects:
  - Project A: Key architecture notes, test commands (`pytest`), deployment targets.
  - Project B: Database schemas, local endpoints, synchronization rules.
- Operational Rules:
  - Keep episodic memories indexed in SQLite FTS5 (`cmem.py`).
  - Supersede conflicting decisions with `--replace`.
  - Maintain clean boundaries between personal local state and shared code.
