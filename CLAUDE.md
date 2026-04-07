# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

clawed-back is a personal AI assistant platform that runs inside Claude Code. It's a white-room reimplementation of the OpenClaw concept — a multi-channel AI assistant with tool execution, automation, and approval workflows — built entirely with Claude Code skills and minimal Python.

## Architecture

Claude Code IS the agent runtime. Python handles only persistent I/O (web server, message queue, voice transcription). Everything else is skills.

### Skill Compatibility
OpenClaw and Claude Code both use the **AgentSkills spec** (Markdown + YAML frontmatter in SKILL.md). OpenClaw/ClawHub skills can be imported via `/oc-hub import <slug>`. The importer strips OpenClaw-specific `metadata.openclaw` fields and adds Claude Code `allowed-tools`. The markdown body (actual instructions) works unchanged.

```
Web UI → FastAPI Server → SQLite Queue → Claude Code (polling) → Response → SSE → Web UI
```

### Hybrid Polling
- **Idle**: CronCreate checks queue every 1 minute
- **Active**: /loop checks every 10 seconds (escalates when user messages within 5 min)
- **De-escalation**: After 5 min idle, drops back to CronCreate

## Tech Stack

- **Python 3.11+** with FastAPI, uvicorn, sse-starlette
- **SQLite** for message queue (WAL mode)
- **Whisper** (turbo model) for voice transcription
- **Claude Code** skills for all intelligence and workflows

## Commands

```bash
# Start server (HTTP)
cd .claude/skills/oc-poll/scripts && source ../.venv/bin/activate && python main.py

# Start server (HTTPS — needs fullchain.pem + privkey.pem in server/)
cd .claude/skills/oc-poll/scripts && source ../.venv/bin/activate && python main.py --ssl

# Start server (HTTPS — custom cert paths)
cd .claude/skills/oc-poll/scripts && source ../.venv/bin/activate && python main.py --public /path/to/cert.pem --private /path/to/key.pem

# Or use the setup wizard
/oc-setup

# Token management
python .claude/skills/oc-poll/scripts/token_manager.py show          # Display current token
python .claude/skills/oc-poll/scripts/token_manager.py regenerate    # Generate new random token
python .claude/skills/oc-poll/scripts/token_manager.py set <token>   # Set custom token (restart server after)

# File management
python .claude/skills/oc-poll/scripts/file_manager.py store <path> --name file.pdf --type generated  # Store a file
python .claude/skills/oc-poll/scripts/file_manager.py get <file_id>       # Get file path by ID
python .claude/skills/oc-poll/scripts/file_manager.py share <file_id>     # Create temp download link (60 min default)
python .claude/skills/oc-poll/scripts/file_manager.py shares              # List active shares
python .claude/skills/oc-poll/scripts/file_manager.py cleanup             # Remove expired shares

# Queue operations (used by skills)
python .claude/skills/oc-poll/scripts/queue_manager.py peek          # Check for messages
python .claude/skills/oc-poll/scripts/queue_manager.py read          # Read next message
python .claude/skills/oc-poll/scripts/queue_manager.py write '<json>' # Send response
python .claude/skills/oc-poll/scripts/queue_manager.py ack <id>      # Mark processed
python .claude/skills/oc-poll/scripts/queue_manager.py history <n>   # Message history
python .claude/skills/oc-poll/scripts/queue_manager.py activity      # Last user activity timestamp
```

## Project Structure

```
data/                # Runtime data (gitignored)
  messages.db        # SQLite queue
  uploads/           # User-uploaded files
  sessions/          # Session state, poll state, automations
  logs/              # Server logs

.claude/skills/      # All skills
  oc-poll/           # Hybrid polling controller (heartbeat)
  oc-router/         # Message routing and dispatch
  oc-session/        # Conversation state management
  oc-respond/        # Response formatting and delivery
  oc-approve/        # Approval gate for dangerous operations
  oc-tools/          # Tool execution coordinator
  oc-voice/          # Voice message processing
  oc-automate/       # Scheduled task management
  oc-webhook/        # Webhook handler
  oc-channel/        # Channel adapter registry
  oc-hub/            # Skill marketplace
  oc-setup/          # First-run setup wizard
  (+ inherited toolkit skills)

.claude/agents/      # Subagents
```

## Available Skills

| Skill | Purpose |
|-------|---------|
| `/start` | Start ClawedBack — ensures server is up, creates polling cron, runs one poll. **Run this whenever restarting Claude Code.** |
| `/oc-update` | Pull latest ClawedBack updates from GitHub, preserving local config/data |
| `/oc-resume` | Resume after restart — starts server, polling, rebuilds config if missing (use if config is lost) |
| `/oc-setup` | First-run setup wizard |
| `/oc-automate` | Schedule tasks and reminders |
| `/oc-hub` | Browse and install skills |
| `/oc-files` | Store, organize, and share files via temporary download links |
| `/oc-token` | View, regenerate, or set a custom auth token |
| `/oc-ssl` | Set up Let's Encrypt SSL certificates via certbot |
| `/oc-local` | Run a task on a local or remote Ollama model. Usage: `/oc-local [optional model] <task>`. Config saved in `data/sessions/ollama_config.json` |
| `/oc-crosstalk` | Send a message to another ClawedBack instance. For short-term, quick exchanges only. Usage: `/oc-crosstalk <ip_or_domain:port> <token> <message>` |
| `/oc-channel` | Manage communication channels |
| `/wizard` | 8-phase production implementation |
| `/tdd` | Test-driven development |
| `/code-review` | Code review via subagent |
| `/research` | Structured web research |
| `/grill-me` | Deep interview before building |

## OpenClaw Tool Compatibility

This project ports OpenClaw. When you encounter an OpenClaw tool reference (from imported ClawHub skills or user requests), **read `.claude/skills/oc-hub/references/tool-mapping.md`** for the correct Claude Code alternative. 19 of 23 tools are matched; 4 are not available (x_search, image_generate, video_generate, canvas) — inform the user and suggest building a skill for those.

## Reference Guides

Guides in `.claude/skills/oc-hub/references/`. Consult when needed:
- **`tool-mapping.md` — ALWAYS read this when converting, importing, or adapting anything from OpenClaw to Claude Code.** It maps every OpenClaw tool to its Claude Code equivalent with exact replacements.
- `02-best-practices.md` — Production patterns
- `03-skills-and-agents.md` — Skill/agent creation
- `04-context-and-memory.md` — Context management
- `05-workflows-and-automation.md` — Hooks, cron, loops

## Resuming After Restart

When starting a new Claude session in this project, **run `/oc-resume` first**. It reads `data/clawedback.json` (written by `/oc-setup`) to know the install mode, Python path, SSL config, port, and claude binary location. If the config file is missing, `/oc-resume` auto-detects the setup from the environment and rebuilds it. The config is only written after the server and polling are confirmed working.

## Responsiveness (IMPORTANT)

### Status Updates
When executing multi-step tasks, plans, or long-running operations, send periodic status updates to the chat via `queue_manager.py write`. Update the user when:
- A step succeeds or fails
- You're trying a different approach
- You're stuck and need help
- You hit a milestone or significant progress point

Don't go silent for extended periods. The user is watching the chat, not the terminal.

### Queue Polling During Tasks
**Check the message queue every few commands**, regardless of what you're doing:
```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py peek
```
If there's a new message, **read and process it before continuing your current task**. The user may be sending mid-task feedback, corrections, a request to stop, or new priority instructions. User messages always take precedence over in-progress work.

## Rules

### Python Environments
NEVER use `--break-system-packages`. Always use the project venv at `.venv/`.

### MCP Server Security Warning
If the user has MCP servers configured, or asks to add one, check whether the server URL is a local address. For ANY non-local/third-party MCP server, issue the security warning and get explicit acknowledgment before proceeding.

### File Boundaries
Skills and tools operate within this project directory. Operations outside require user approval via the oc-approve gate.

### Message Queue Protocol
All communication between the web UI and Claude Code goes through the SQLite queue. Never bypass it — the queue is the single source of truth for message state.

### Read Receipts
When a message is read (`queue_manager.py read` sets processed=1) or acknowledged (`ack` sets processed=2), the SSE stream emits a `read_receipt` event. The web UI shows a green checkmark. This is automatic — no extra steps needed.

### SSL
The server supports HTTPS via `--ssl` (looks for `fullchain.pem`/`privkey.pem` in `server/`) or `--public`/`--private` flags for custom cert paths. Falls back to HTTP if certs are missing.

### Auth
The server uses bearer token auth. The token is auto-generated on first run and stored at `data/.auth_token`. Never log or expose it in responses.
