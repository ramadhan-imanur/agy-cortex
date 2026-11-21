# Hermes-Lite Persistent Memory Protocol

You have a lightweight, zero-RAM persistent memory system modeled after Hermes Agent.
- **Core Memory (Injected Below):** `USER.md` (max 1500 chars) and `MEMORY.md` (max 2500 chars) are loaded automatically upon compilation.
- **Episodic Search (On-Demand):** Do not guess past project history. Search the SQLite FTS5 archive in <5ms when needed:
  `python ~/.gemini/config/memory/hmem.py search "<keywords>"` (or `hmem search "<keywords>"`)
- **Save / Supersede Decisions:** After completing a milestone, solving a non-trivial bug, or changing a rule, record it:
  - Detailed/episodic record: `python ~/.gemini/config/memory/hmem.py add --project "<name>" --category "<decision|progress|bugfix|note>" --title "<short title>" --content "<concise details>" [--replace]`
  - Use `--replace` when updating an existing rule/decision so old rules never collide.
  - Core snapshot update (`USER.md` / `MEMORY.md`): update via `hmem core-set <user|memory> --file <tmp>` (strict char cap enforced; consolidate old entries if near limit).
- **Cross-Device & Workspace Continuity:**
  - Prefer `hmem search --project "<name>"`, `git status`, and project graphs over creating bloated `PROGRESS.md` changelogs.
  - If an existing `PROGRESS.md` or state doc is updated, overwrite stale rules in place with only the latest compact decisions; run `hmem sync-disk` after key milestones when portable storage is mounted.
- **Accessibility & Directness:** Match reply length to the weight of the ask: clear claims, structured tables, and clean Markdown without conversational filler.

---

## Core Snapshot: USER.md (Template)

- User: <your_name>, Timezone: <UTC_OFFSET>.
- Workflow & Rhythm: Work hours <START_TIME> - <END_TIME>.
- Communication Style: Concise, direct, clean tables, screen-reader friendly.
- Core Priorities:
  1. Priority 1: <Main Academic / Work Goal>
  2. Priority 2: <Health / Fitness Habit>
  3. Priority 3: <Key Project / Initiative>

---

## Core Snapshot: MEMORY.md (Template)

- Machine & Runtime: Hostname `<HOSTNAME>`, OS: `<OS>`, Python `<VERSION>`, key CLIs: `git`, `uv`, `rg`.
- Network & Remote: Active endpoints and development hosts.
- Storage & Workspaces: Main code repository paths and portable backup mounts.
- Operational Rules:
  - Keep episodic memories indexed in SQLite FTS5 (`hmem`).
  - Supersede conflicting decisions with `--replace`.
  - Maintain thin orchestrators and enforce modular file limits.
