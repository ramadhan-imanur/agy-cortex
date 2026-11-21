---
name: cortex-memory
description: Manage Antigravity's lightweight persistent memory: search episodic SQLite FTS5 history across sessions, record/supersede project decisions and bugfixes, sync cross-device via portable storage, and update/self-compact bounded USER.md and MEMORY.md core snapshots. Use whenever restoring past context, recording long-term project progress, or switching between development devices.
---

# Cortex Memory Skill

CLI path: `python ~/.gemini/config/memory/cmem.py` (Windows) or `python3 ~/.gemini/config/memory/cmem.py` (Linux / macOS).

## Quick Reference

| Action | Command |
| :--- | :--- |
| **Search past memories (BM25 <5ms)** | `python ~/.gemini/config/memory/cmem.py search "<keywords>" [--project <name>] [--limit 5]` |
| **List recent memories** | `python ~/.gemini/config/memory/cmem.py recent [--project <name>] [--limit 8]` |
| **List tracked projects** | `python ~/.gemini/config/memory/cmem.py projects` |
| **Record or replace decision/progress** | `python ~/.gemini/config/memory/cmem.py add --project "<name>" --category "<decision\|progress\|bugfix\|note\|convention>" --title "<title>" --content "<details>" [--replace]` |
| **Sync two-way with portable storage** | `python ~/.gemini/config/memory/cmem.py sync-disk` |
| **Inspect core snapshot & char limits** | `python ~/.gemini/config/memory/cmem.py core-show` |
| **Update core snapshot (enforces cap)** | `python ~/.gemini/config/memory/cmem.py core-set <user\|memory> --file <tmp_file>` (or `--content -`) |
| **Re-sync plugin `AGENTS.md`** | `python ~/.gemini/config/memory/cmem.py sync` |

## Rules and Anti-Bloat Discipline

1. **Core Snapshot Caps:** `USER.md` max `1500` chars; `MEMORY.md` max `2500` chars. Keep machine-specific hardware and paths inside local `MEMORY.md` (never overwritten across devices) and keep `USER.md` OS-neutral.
2. **Supersede, Never Stack Contradictions:** Use `--replace` when updating an existing rule or decision so old agreements do not collide with new ones.
3. **Avoid Bloated `PROGRESS.md` Changelogs:** Do not create sprawling `PROGRESS.md` files across projects. Prefer `cmem.py search --project <name>` (<5ms) and `git status`. If an existing state doc is updated, overwrite stale rules in place with only the latest compact decisions.
4. **Cross-Device Sync:** Run `cmem.py sync-disk` after finishing major project work while portable storage is mounted (`pulse.py` also runs it automatically).
