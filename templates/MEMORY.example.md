# Core Snapshot: Machine & Project Memory (Keep <= 2500 characters)

- Machine & Runtime: Hostname `<HOSTNAME>`, OS: `<OS>`, Python `<VERSION>`, key CLIs: `git`, `uv`, `rg`.
- Network & Remote: Active services, development environments, and endpoints.
- Storage & Workspaces: Main code repository paths, portable disk mount points, and backup targets.
- Active Projects:
  - Project A: Key architectural patterns, test commands (`pytest`), deployment targets.
  - Project B: Database schemas, local endpoints, synchronization scripts.
- Operational Rules:
  - Keep episodic memories indexed in SQLite FTS5 (`hmem`).
  - Supersede conflicting decisions with `--replace`.
  - Maintain thin orchestrators and enforce modular file limits.
