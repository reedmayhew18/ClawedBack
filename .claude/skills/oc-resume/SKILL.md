---
name: oc-resume
description: "Resume ClawedBack after a restart. Starts the web server, resumes polling, and rebuilds config if missing. Use when starting a new Claude session in an existing ClawedBack install, or when the user says 'resume', 'start', 'restart', 'begin polling', or 'oc-resume'."
allowed-tools: "Read Write Edit Bash Grep Glob"
---

# Resume ClawedBack

Restart the server and polling after a Claude Code session restart. Self-healing — if the config file is missing, it detects the setup and rebuilds it.

## Step 1: Locate the project

```bash
PROJECT_ROOT="$(pwd)"
echo "Project root: $PROJECT_ROOT"
ls "$PROJECT_ROOT/.claude/skills/oc-poll/scripts/main.py" 2>/dev/null && echo "Server found" || echo "ERROR: Not in an ClawedBack project directory"
```

If `.claude/skills/oc-poll/scripts/main.py` doesn't exist, tell the user to `cd` into their ClawedBack directory first. **STOP.**

## Step 2: Check for existing config

```bash
cat "$PROJECT_ROOT/data/clawedback.json" 2>/dev/null || echo "NO_CONFIG"
```

**If config exists** → skip to Step 5 (use the saved config).

**If NO_CONFIG** → proceed to Step 3 (auto-detect and rebuild).

## Step 3: Auto-detect the setup

Run all of these to determine the environment:

```bash
# Who are we?
echo "USER=$(whoami)"
echo "UID=$(id -u)"

# Are we in tmux?
[ -n "$TMUX" ] && echo "TMUX=yes" || echo "TMUX=no"

# Is IS_SANDBOX set?
[ "$IS_SANDBOX" = "1" ] && echo "SANDBOX=yes" || echo "SANDBOX=no"

# Is there a venv?
[ -d "$PROJECT_ROOT/.venv" ] && echo "VENV=yes" || echo "VENV=no"

# What Python are we using?
which python3

# Can we find the venv python?
[ -f "$PROJECT_ROOT/.venv/bin/python" ] && echo "VENV_PYTHON=$PROJECT_ROOT/.venv/bin/python" || echo "VENV_PYTHON=none"

# Is FastAPI importable from system python?
python3 -c "import fastapi" 2>/dev/null && echo "SYSTEM_FASTAPI=yes" || echo "SYSTEM_FASTAPI=no"

# Is FastAPI importable from venv python?
[ -f "$PROJECT_ROOT/.venv/bin/python" ] && "$PROJECT_ROOT/.venv/bin/python" -c "import fastapi" 2>/dev/null && echo "VENV_FASTAPI=yes" || echo "VENV_FASTAPI=no"

# SSL certs?
[ -f "$PROJECT_ROOT/.claude/skills/oc-poll/scripts/fullchain.pem" ] && echo "SSL_LOCAL=yes" || echo "SSL_LOCAL=no"
ls /etc/letsencrypt/live/*/fullchain.pem 2>/dev/null | head -1 || echo "SSL_LETSENCRYPT=none"

# What port?
echo "PORT=${OC_PORT:-8080}"

# Host URL — check env, then detect adapter IP
echo "HOST_URL=${OC_HOST_URL:-}"
hostname -I 2>/dev/null | awk '{print "ADAPTER_IP=" $1}' || ip -4 addr show scope global | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1 | xargs -I{} echo "ADAPTER_IP={}"

# Whisper config?
echo "WHISPER_MODEL=${OC_WHISPER_MODEL:-turbo}"
echo "WHISPER_DEVICE=${OC_WHISPER_DEVICE:-auto}"

# Non-root users on the system
ls /home/ 2>/dev/null

# Is the server already running?
curl -sk http://localhost:${OC_PORT:-8080}/api/health 2>/dev/null || echo "SERVER_DOWN"

# Claude binary location
command -v claude 2>/dev/null || echo "$HOME/.local/bin/claude"
```

## Step 4: Determine mode from detection

Use this logic:

```
if UID == 0:
    if IS_SANDBOX == 1:
        MODE = "c"    # System install, root, no venv, no permissions
    else:
        MODE = "b"    # Portable root with venv
else:
    MODE = "a"        # Portable user with venv
```

For the Python command:
```
if MODE == "c" (no venv):
    PYTHON = "python3"
    PIP_FLAGS = "--break-system-packages"
else:
    PYTHON = "$PROJECT_ROOT/.venv/bin/python"
    # Verify venv python works:
    $PYTHON -c "import fastapi" || PYTHON = "python3"  # fallback
```

For SSL, check in order:
1. Let's Encrypt certs at `/etc/letsencrypt/live/*/` → use `--public` and `--private` with those paths
2. Local certs at `.claude/skills/oc-poll/scripts/fullchain.pem` and `.claude/skills/oc-poll/scripts/privkey.pem` → use `--ssl`
3. Neither → no SSL (HTTP)

For the non-root username (Mode B/C):
- Check `ls /home/` for a single user → use that
- If multiple users, check `data/sessions/install_mode.json` for a saved username
- If still unknown, ask the user

For the claude binary:
```bash
CLAUDE_BIN="$(command -v claude 2>/dev/null || echo "$HOME/.local/bin/claude")"
# For root, also check the non-root user's path:
[ "$(id -u)" -eq 0 ] && [ -f "/home/$USERNAME/.local/bin/claude" ] && CLAUDE_BIN="/home/$USERNAME/.local/bin/claude"
```

## Step 5: Start the server

First check if it's already running:
```bash
curl -sk http://localhost:${OC_PORT:-8080}/api/health 2>/dev/null
```

If health check succeeds → server is already running, skip to Step 6.

If not running, build the server command from the config (or detected values):

First kill any leftover server process:
```bash
pkill -f "python3 main.py" 2>/dev/null || true
sleep 1
```

**Mode A (user, venv):**
```bash
cd "$PROJECT_ROOT/.claude/skills/oc-poll/scripts" && source "$PROJECT_ROOT/.venv/bin/activate"
nohup python main.py $SSL_FLAGS > "$PROJECT_ROOT/data/logs/server.log" 2>&1 &
sleep 1 && pgrep -f "python3 main.py" | tail -1 > "$PROJECT_ROOT/data/server.pid"
```

**Mode B (root, venv):**
```bash
cd "$PROJECT_ROOT/.claude/skills/oc-poll/scripts" && source "$PROJECT_ROOT/.venv/bin/activate"
nohup python main.py $SSL_FLAGS > "$PROJECT_ROOT/data/logs/server.log" 2>&1 &
sleep 1 && pgrep -f "python3 main.py" | tail -1 > "$PROJECT_ROOT/data/server.pid"
```

**Mode C (root, system python):**
```bash
cd "$PROJECT_ROOT/.claude/skills/oc-poll/scripts"
nohup python3 main.py $SSL_FLAGS > "$PROJECT_ROOT/data/logs/server.log" 2>&1 &
sleep 1 && pgrep -f "python3 main.py" | tail -1 > "$PROJECT_ROOT/data/server.pid"
```

Where `$SSL_FLAGS` is:
- No SSL: (empty)
- Local SSL: `--ssl`
- Let's Encrypt: `--public /etc/letsencrypt/live/$DOMAIN/fullchain.pem --private /etc/letsencrypt/live/$DOMAIN/privkey.pem`

**Verify it started:**
```bash
sleep 3
kill -0 $(cat "$PROJECT_ROOT/data/server.pid") 2>/dev/null && echo "Process alive" || echo "PROCESS DIED"
curl -sk http://localhost:${OC_PORT:-8080}/api/health
```

If it died, show the log:
```bash
tail -30 "$PROJECT_ROOT/data/logs/server.log"
```
Help debug. **STOP** if server won't start.

## Step 6: Start polling

```
CronCreate with cron "*/1 * * * *" and prompt "/oc-poll"
```

Verify with CronList.

## Step 6.5: Recover interrupted workflows

Check for any in-progress approval chains that were interrupted by the crash:

```bash
cat "$PROJECT_ROOT/data/sessions/workflows.json" 2>/dev/null
```

If any workflow has `"status": "in_progress"`, find the step with `"status": "pending"`. Re-queue that step's approval request:

```bash
cd "$PROJECT_ROOT/.claude/skills/oc-poll/scripts" && python queue_manager.py write '{
  "content": "**Resumed workflow: WORKFLOW_NAME** (Step N/M)\n\nThis workflow was interrupted and is resuming.\n\nNext action: STEP_DESCRIPTION\n```\nSTEP_COMMAND\n```\n\nApprove? Reply **yes** or **no**.",
  "type": "approval_request",
  "metadata": {"workflow_id": "ID", "step": N, "total_steps": M}
}'
```

If no `workflows.json` exists or no workflows are in progress, skip this step.

## Step 7: Run one poll cycle to confirm everything works

```bash
cd "$PROJECT_ROOT/.claude/skills/oc-poll/scripts" && $PYTHON queue_manager.py peek
```

If this returns valid JSON (`{"pending": N}`), the whole stack is working.

## Step 8: Write config (only after everything works)

Only write the config file AFTER Steps 5-7 all succeeded. This way a broken config is never persisted.

Write `data/clawedback.json`:

```bash
cat > "$PROJECT_ROOT/data/clawedback.json" << JSONEOF
{
  "mode": "$MODE",
  "project_root": "$PROJECT_ROOT",
  "username": "$USERNAME",
  "host_url": "$HOST_URL",
  "python": "$PYTHON",
  "claude_bin": "$CLAUDE_BIN",
  "port": ${OC_PORT:-8080},
  "ssl": {
    "enabled": $SSL_ENABLED,
    "cert": "$SSL_CERT",
    "key": "$SSL_KEY"
  },
  "whisper": {
    "model": "${OC_WHISPER_MODEL:-turbo}",
    "device": "${OC_WHISPER_DEVICE:-auto}"
  },
  "server_cmd": "$SERVER_CMD",
  "resume_cmd": "$RESUME_CMD",
  "configured_at": "$(date -Iseconds)"
}
JSONEOF
```

Where:
- `$HOST_URL` is the adapter IP (auto-detected from `hostname -I`), or from `OC_HOST_URL` env var, or from the previous config. Falls back to adapter IP if unknown.
- `$SSL_ENABLED` is `true` or `false`
- `$SSL_CERT` / `$SSL_KEY` are the cert paths or empty strings
- `$SERVER_CMD` is the full command to start the server (for future reference)
- `$RESUME_CMD` is the full tmux command to restart ClawedBack:
  - Mode A: `tmux new -s clawedback 'cd $PROJECT_ROOT && claude'`
  - Mode B: `tmux new -s clawedback 'cd $PROJECT_ROOT && sudo -E $CLAUDE_BIN'`
  - Mode C: `tmux new -s clawedback 'cd $PROJECT_ROOT && sudo -E $CLAUDE_BIN --dangerously-skip-permissions'`

## Step 9: Summary

```
ClawedBack resumed!

Mode: $MODE_NAME
Server: $PROTOCOL://localhost:$PORT (PID: $PID)
Polling: CronCreate every 1 minute
Auth token: (run /oc-token to view)

To reconnect to this tmux session later:
  tmux attach -t clawedback
```

If tmux wasn't detected, warn:
```
WARNING: You are not in tmux. Polling will stop when this terminal closes.
To fix: exit, then run:
  $RESUME_CMD
```

---

## Using the Config (for other skills)

Any skill can read the config to find paths and settings:

```bash
cat "$PROJECT_ROOT/data/clawedback.json"
```

Or specific fields:
```bash
python3 -c "import json; c=json.load(open('$PROJECT_ROOT/data/clawedback.json')); print(c['python'])"
```
