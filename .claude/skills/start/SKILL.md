---
name: start
description: "Start ClawedBack — ensures the web server is running, creates the polling cron job, and runs one poll cycle. Use when starting or restarting Claude Code in a ClawedBack project, or when the user says 'start', '/start', 'begin', or 'get going'."
allowed-tools: "Read Write Bash Grep Glob"
---

# Start ClawedBack

Run this whenever starting or restarting Claude Code in a ClawedBack installation. It ensures everything is up and running.

## Step 1: Locate the project and config

```bash
PROJECT_ROOT="$(pwd)"
cat "$PROJECT_ROOT/data/clawedback.json" 2>/dev/null || echo "NO_CONFIG"
```

If no config exists, tell the user to run `/oc-setup` first (first-time install) or `/oc-resume` (if config was lost and needs rebuilding). **STOP.**

If config exists, read the mode, python path, server command, and port from it.

## Step 2: Ensure the web server is running

```bash
curl -sk http://localhost:${OC_PORT:-8080}/api/health 2>/dev/null
```

**If health check succeeds** — server is already running, skip to Step 3.

**If server is down** — start it using the saved `server_cmd` from the config:

```bash
pkill -f "python3 main.py" 2>/dev/null || true
sleep 1
```

Then start the server (read the exact command from `clawedback.json`'s `server_cmd` field):

```bash
nohup $SERVER_CMD > $PROJECT_ROOT/data/logs/server.log 2>&1 &
sleep 2 && pgrep -f "python3 main.py" | tail -1 > $PROJECT_ROOT/data/server.pid
```

Verify:
```bash
curl -sk http://localhost:${OC_PORT:-8080}/api/health
```

If still failing, show the log:
```bash
tail -20 $PROJECT_ROOT/data/logs/server.log
```

## Step 3: Create the polling cron job

```
CronCreate with cron "*/1 * * * *" and prompt "/oc-poll"
```

This schedules the heartbeat. No need to check if one already exists — CronCreate handles that.

## Step 4: Run one poll cycle

Run `/oc-poll` once immediately to process any messages that came in while Claude was offline.

## Step 5: Confirm

Tell the user:
```
ClawedBack started.
Server: [URL from config]
Polling: active (every 1 minute)
```

Keep it short. They know what it does.
