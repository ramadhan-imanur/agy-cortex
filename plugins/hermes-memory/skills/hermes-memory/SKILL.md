---
name: hermes-memory
description: Manage Antigravity's lightweight Hermes-style persistent memory: search episodic SQLite FTS5 history across sessions, record/supersede project decisions and bugfixes, sync cross-device via portable storage, and update/self-compact bounded USER.md and MEMORY.md core snapshots. Use whenever restoring past context, recording long-term project progress, or switching between development devices.
---

# Hermes-Lite Memory Skill

CLI path: `hmem` (Windows wrapper) or `python3 ~/.gemini/config/memory/hmem.py` (Ubuntu / cross-OS).

## Quick Reference

| Action | Command |
| :--- | :--- |
| **Search past memories (BM25 <5ms)** | `hmem search "<keywords>" [--project <name>] [--limit 5]` |
| **List recent memories** | `hmem recent [--project <name>] [--limit 8]` |
| **List tracked projects** | `hmem projects` |
| **Record or replace decision/progress** | `hmem add --project "<name>" --category "<decision\|progress\|bugfix\|note\|convention>" --title "<title>" --content "<details>" [--replace]` |
| **Sync two-way with portable storage** | `hmem sync-disk` |
| **Inspect core snapshot & char limits** | `hmem core-show` |
| **Update core snapshot (enforces cap)** | `hmem core-set <user\|memory> --file <tmp_file>` (or `--content -`) |
| **Re-sync plugin `AGENTS.md`** | `hmem sync` |

## Rules & Anti-Bloat Discipline

1. **Core Snapshot Caps:** `USER.md` max `1500` chars; `MEMORY.md` max `2500` chars. Keep machine-specific hardware/paths inside local `MEMORY.md` (never overwritten across devices) and keep `USER.md` OS-neutral.
2. **Supersede, Never Stack Contradictions:** Use `--replace` when updating an existing rule/decision in `hmem` so old agreements do not collide with new ones.
3. **Avoid Bloated `PROGRESS.md` Changelogs:** Do not create sprawling `PROGRESS.md` files across projects. Prefer `hmem search --project <name>` (<5ms) + `git status` + project knowledge graph. If an existing state doc is updated, overwrite stale rules in place with only the latest compact decisions.
4. **Cross-Device Sync:** Run `hmem sync-disk` after finishing major project work while portable storage is mounted (`heartbeat.py` also runs it automatically).
