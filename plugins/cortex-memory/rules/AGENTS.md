# Cortex Persistent Memory Protocol

You have a lightweight, zero-RAM persistent memory system built natively for Antigravity.

- **Core Memory (Injected Below):** `USER.md` (max 1500 chars) and `MEMORY.md` (max 2500 chars) are loaded automatically upon compilation.
- **Episodic Search (On-Demand):** Do not guess past project history. Search the SQLite FTS5 archive in <5ms when needed:
  `python ~/.gemini/config/memory/cmem.py search "<keywords>"`
- **Save / Supersede Decisions:** After completing a milestone, solving a non-trivial bug, or changing a rule, record it:
  - Detailed/episodic record: `python ~/.gemini/config/memory/cmem.py add --project "<name>" --category "<decision|progress|bugfix|note|convention>" --title "<short title>" --content "<concise details>" [--replace]`
  - Use `--replace` when updating an existing rule or decision so old rules never collide.
  - Core snapshot update (`USER.md` / `MEMORY.md`): update via `python ~/.gemini/config/memory/cmem.py core-set <user|memory> --file <tmp>` (strict char cap enforced; consolidate old entries if near limit).
- **Cross-Device and Workspace Continuity:**
  - Prefer `cmem.py search --project "<name>"` and `git status` over creating sprawling `PROGRESS.md` changelogs.
  - If an existing `PROGRESS.md` or state document is updated, overwrite stale entries in place with only the latest compact decisions; run `cmem.py sync-disk` after key milestones when portable storage is mounted.
- **Directness:** Match reply length to the weight of the ask with plain claims, clear headings, and concise tables.

---

## Core Snapshot: USER.md (Template)

- User: `<your_name>`, Timezone: `<UTC_OFFSET>`.
- Workflow and Rhythm: Work hours `<START_TIME>` to `<END_TIME>`.
- Communication Style: Concise, direct, clean tables.
- Core Priorities:
  1. `<Primary Work or Study Goal>`
  2. `<Key Project or Initiative>`

---

## Core Snapshot: MEMORY.md (Template)

- Machine and Runtime: Hostname `<HOSTNAME>`, OS `<OS>`, Python `<VERSION>`, key CLIs: `git`, `rg`.
- Storage and Workspaces: Main workspace directories and portable backup mounts.
- Operational Rules:
  - Keep episodic memories indexed in SQLite FTS5 (`cmem.py`).
  - Supersede conflicting decisions with `--replace`.
  - Keep core snapshots within character bounds.
