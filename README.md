# agy-cortex

Persistent memory engine and local heartbeat daemon for Antigravity agents.

## Overview

`agy-cortex` provides long-term episodic memory, bounded context snapshots, and background system health checks for Antigravity. It runs locally with zero RAM overhead during idle periods and performs scheduled checks without invoking LLM tokens.

## Architecture

The system consists of three modular layers:

### 1. Hermes Memory Engine (`plugins/hermes-memory` and `scripts/hmem.py`)
- **Core Snapshots:** Keeps `USER.md` (max 1500 characters) and `MEMORY.md` (max 2500 characters) in sync across sessions.
- **Episodic SQLite Archive:** Stores decisions, bugfixes, progress notes, and conventions in a local SQLite database indexed with FTS5 for sub-5ms BM25 full-text retrieval.
- **Conflict Prevention:** Uses `--replace` flags to update existing rules instead of stacking contradictory instructions.
- **Cross-Device Sync:** Supports bidirectional synchronization across machines using portable storage.

### 2. OpenClaw Operational Layer (`plugins/openclaw-ops` and `scripts/heartbeat.py`)
- **Proactive Heartbeat:** Runs periodic checks on disk capacity, available RAM, swap usage, and critical services via Windows Task Scheduler or systemd user timers.
- **Zero Token Idle:** Operates entirely with deterministic Python scripts without background LLM calls.
- **Cooldown Notifications:** Desktop alerts trigger only when monitored thresholds are breached, avoiding notification spam.
- **Progress Tracking:** Scans and indexes updated `PROGRESS.md` files from project workspaces once every 24 hours.

### 3. Universal Modular Standard (`plugins/universal-modular-standard`)
- Enforces modular design constraints across all languages: maximum 150 lines of code per module, thin orchestrators under 80 lines, and 5-layer orthogonal decomposition.
- Includes a LaTeX modular compilation workflow with index caching.

## Agent Workflow

The interaction lifecycle follows a structured three-phase execution loop:

### 1. Session Boot and Context Ingestion
- Antigravity loads the core protocol from `rules/AGENTS.md`.
- Active constraints and preferences from `USER.md` (capped at 1500 characters) and environment state from `MEMORY.md` (capped at 2500 characters) are injected directly into the session.
- The session starts immediately without reading historical project logs.

### 2. Task Execution and Episodic Retrieval
- **On-Demand Search:** When context about past conventions, bugfixes, or prior architecture is needed, the agent runs `hmem search "<keywords>"`. Relevant snippets return in under 5 milliseconds from the local SQLite FTS5 index.
- **Rule Superseding:** When an agreement changes, the agent records the update with `hmem add --project "<name>" --category "<type>" --title "<title>" --content "<text>" --replace`. This overwrites stale entries and prevents contradictory instructions.
- **Snapshot Updates:** Milestones or critical rule adjustments are committed back to `USER.md` or `MEMORY.md` using `hmem core-set`, which strictly enforces character limits.

### 3. Background Maintenance and Heartbeat
- **Scheduled Monitoring:** The host operating system runs `heartbeat.py` every 30 minutes (0 MB idle, 0 LLM tokens).
- **System Checks:** Verifies disk usage, free RAM, swap limits, and background task health. Alerts emit desktop notifications only when predefined thresholds fail.
- **Automated Workspace Indexing:** Every 24 hours, modified `PROGRESS.md` documents across project directories are indexed into the SQLite archive.
- **Storage Synchronization:** When portable storage is mounted, `hmem sync-disk` runs in quiet mode to keep episodic records and citations consistent across machines.

## Setup and Installation

### 1. Install Plugins and Scripts
On Windows (PowerShell):
```powershell
# Copy plugins into your Antigravity config directory
Copy-Item -Path "plugins\*" -Destination "$HOME\.gemini\config\plugins\" -Recurse -Force

# Copy scripts into your local memory directory
New-Item -ItemType Directory -Path "$HOME\.gemini\config\memory" -Force
Copy-Item -Path "scripts\hmem.py" -Destination "$HOME\.gemini\config\memory\hmem.py"
```

On Linux:
```bash
# Copy plugins into ~/.gemini/config/plugins/
mkdir -p ~/.gemini/config/plugins ~/.gemini/config/memory
cp -r plugins/* ~/.gemini/config/plugins/
cp scripts/hmem.py ~/.gemini/config/memory/hmem.py
chmod +x ~/.gemini/config/memory/hmem.py
```

### 2. Initialize Memory Snapshots
Copy the example templates:
```bash
cp templates/USER.example.md ~/.gemini/config/memory/USER.md
cp templates/MEMORY.example.md ~/.gemini/config/memory/MEMORY.md
cp templates/HEARTBEAT.example.md ~/.gemini/config/memory/HEARTBEAT.md
```
Edit `USER.md` and `MEMORY.md` with your preferences and machine details.
Compile them into the agent rules:
```bash
python ~/.gemini/config/memory/hmem.py init
```

### 3. Configure the Scheduled Heartbeat
- **Windows:** Create a task in Task Scheduler named `AntigravityHeartbeat` that runs `python path\to\scripts\heartbeat.py` every 30 minutes.
- **Linux:** Create a systemd user timer `agy-heartbeat.timer` executing `scripts/heartbeat.py` every 30 minutes.

### 4. Basic CLI Usage
```bash
# Search episodic memory
python scripts/hmem.py search "database migration"

# Add or update a project decision
python scripts/hmem.py add --project "my-app" --category "decision" --title "JWT expiration" --content "Set JWT token lifetime to 15 minutes." --replace

# Run heartbeat status check
python scripts/heartbeat.py --report
```

## Privacy Model
All episodic memory (`memory.db`), personal snapshots (`USER.md`, `MEMORY.md`), and local operational logs are explicitly excluded via `.gitignore`. The repository contains only generic configurations, schemas, and automation scripts.

## License
MIT
