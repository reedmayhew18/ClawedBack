---
name: oc-token
description: "View, regenerate, or set the auth token for the web chat. Use when the user says 'change token', 'reset token', 'show token', 'set password', 'new token', or 'auth token'."
allowed-tools: "Bash(python*)"
---

# Token Manager

View, regenerate, or set a custom auth token for the ClawedBack web chat.

## Commands

### Show current token
```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python token_manager.py show
```

### Generate a new random token
```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python token_manager.py regenerate
```

### Set a custom token
```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python token_manager.py set "my-custom-token"
```

## After Changing the Token

The server must be restarted for the new token to take effect:

```bash
pkill -f "python3 main.py" 2>/dev/null || true
sleep 2
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts
nohup python3 main.py > $PROJECT_ROOT/data/logs/server.log 2>&1 &
sleep 1 && pgrep -f "python3 main.py" | tail -1 > $PROJECT_ROOT/data/server.pid
```

(Include `--public`/`--private` flags if SSL is configured — check CLAUDE.md for the correct server start command.)

The user will need to re-enter the new token in their browser.

## Important

When the user wants to set a custom token, remind them:

> **Note:** This token is sent over the network to authenticate with the chat. Don't reuse a password you use for important accounts. Pick something unique — it's just an access token, not a login credential.

Token must be at least 8 characters.
