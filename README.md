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

## Repository Layout

```text
agy-cortex/
├── plugins/
│   ├── hermes-memory/              # Hermes persistent memory plugin
│   ├── openclaw-ops/               # OpenClaw heartbeat operations plugin
│   └── universal-modular-standard/ # Modular architecture rules and LaTeX skill
├── scripts/
│   ├── hmem.py                     # Hermes CLI engine for episodic SQLite FTS5 search
│   └── heartbeat.py                # Deterministic heartbeat monitor
└── templates/
    ├── USER.example.md             # Core user profile template (max 1500 chars)
    ├── MEMORY.example.md           # Core machine and workspace template (max 2500 chars)
    ├── HEARTBEAT.example.md        # Thresholds and service checklist
    ├── config.example.json         # Global Antigravity settings template
    └── mcp_config.example.json     # MCP server configuration template
```

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
