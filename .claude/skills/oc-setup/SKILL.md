---
name: oc-setup
description: "First-run setup wizard for clawed-back. Use when the user says 'setup', 'start clawed-back', 'initialize', or when running for the first time. Offers three install modes: portable user, portable root, or system install."
allowed-tools: "Read Write Edit Bash Glob Grep"
---

# Setup Wizard

First-run configuration for clawed-back. Gets everything running.

---

## Phase 1: Choose Install Mode

Present these three options and ask the user to pick one:

**Mode A: Portable Install — User (Recommended)**
- Python venv inside the project folder, runs as normal user
- Claude asks permission before risky operations
- Best for: trying it out, development, personal use

**Mode B: Portable Install — Root**
- Python venv inside the project folder, runs as root
- Full system access, still asks before destructive ops
- Best for: dedicated server/VM needing elevated access

**Mode C: System Install — Root, No Venv**
- System Python (`--break-system-packages`), root, `--dangerously-skip-permissions`
- No permission prompts, no safety net
- Best for: sandboxes, VMs, containers ONLY

> **Mode C WARNING**: Only for systems that are fully backed up, sandboxed, or designated for this purpose. Claude gets unrestricted root access with zero confirmation prompts.

Record the user's choice. All subsequent steps reference this as `MODE`.

---

## Phase 2: Pre-flight Checks

Run ALL of these and evaluate results before proceeding. Stop on any failure.

### 2.1: Set PROJECT_ROOT

```bash
echo "PROJECT_ROOT=$(pwd)"
```

Use this absolute path for all `$PROJECT_ROOT` references throughout setup.

### 2.2: Check Python

```bash
python3 --version
```

If Python < 3.11 or not found: **STOP**. Tell the user to install Python 3.11+.

### 2.3: Check tmux is installed

```bash
which tmux 2>/dev/null && echo "installed" || echo "not found"
```

If not found — install it:
- If root or sudo available: `sudo apt install -y tmux 2>/dev/null || apt install -y tmux 2>/dev/null || sudo dnf install -y tmux 2>/dev/null`
- If install fails, tell the user to install tmux manually for their OS and re-run `/oc-setup`. **STOP.**

### 2.4: Check we're inside tmux

```bash
[ -n "$TMUX" ] && echo "in tmux" || echo "not in tmux"
```

If **NOT in tmux** — **STOP.** Tell the user:

> ClawedBack requires tmux to keep the polling loop alive. Exit this session and restart inside tmux:
>
> ```
> tmux new -s clawedback
> cd PROJECT_ROOT
> CLAUDE_COMMAND
> ```
> Then run `/oc-setup` again.

Where `CLAUDE_COMMAND` is:
- Mode A: `claude`
- Mode B: `sudo -E "$(command -v claude || echo ~/.local/bin/claude)"`
- Mode C: `sudo -E "$(command -v claude || echo ~/.local/bin/claude)" --dangerously-skip-permissions`

Replace `PROJECT_ROOT` with the actual path from 2.1.

### 2.5: Check root status (Mode B/C only)

```bash
id -u
```

If Mode B or C and NOT root (id != 0): **STOP.** Tell the user:

**Mode B:**
> You need to restart as root:
> ```
> sudo -E "$(command -v claude || echo ~/.local/bin/claude)"
> ```

**Mode C:**
> You need to set the sandbox flag and restart:
> ```
> echo 'export IS_SANDBOX=1' >> ~/.bashrc && source ~/.bashrc
> sudo bash -c 'echo "export IS_SANDBOX=1" >> /root/.bashrc'
> sudo -E "$(command -v claude || echo ~/.local/bin/claude)" --dangerously-skip-permissions
> ```

### 2.6: Get the non-root username (Mode B/C only)

If running as root, ask: **"What is the regular (non-root) username on this system?"**

Help them by showing:
```bash
ls /home/
```

Store this as `USERNAME` — used for `sudo -u` commands and CLAUDE.md.

### 2.7: Check if port 8080 is available

```bash
ss -tlnp 2>/dev/null | grep ':8080 ' || echo "port 8080 is free"
```

If port 8080 is in use, tell the user. They can either stop the other service or set `OC_PORT` to a different port:
```bash
export OC_PORT=8090
```

---

## Phase 3: Install Dependencies

### Mode A & B: Create venv and install

```bash
cd $PROJECT_ROOT && python3 -m venv .venv
source .venv/bin/activate
pip install -r .claude/skills/oc-poll/scripts/requirements.txt
```

**Verify installation succeeded:**
```bash
python -c "import fastapi; import sse_starlette; print('OK')"
```

If that fails, **STOP** — show the pip error output and help debug.

### Mode C: Install into system Python

```bash
pip install --break-system-packages -r $PROJECT_ROOT/.claude/skills/oc-poll/scripts/requirements.txt
```

**Verify:**
```bash
python3 -c "import fastapi; import sse_starlette; print('OK')"
```

If that fails, **STOP**.

---

## Phase 4: Whisper Setup (Voice Messages)

Ask: **"Do you want voice messages? This requires OpenAI Whisper."**

If no — skip to Phase 5.

If yes — check if PyTorch exists:

```bash
python3 -c "import torch; print('cuda:', torch.cuda.is_available())" 2>/dev/null
```

**First, install ffmpeg** (required by whisper):
```bash
which ffmpeg 2>/dev/null && echo "ffmpeg installed" || apt install -y ffmpeg 2>/dev/null || sudo apt install -y ffmpeg
```

If apt isn't available: `dnf install -y ffmpeg` (Fedora) or `pacman -S ffmpeg` (Arch) or `brew install ffmpeg` (macOS).

**If PyTorch is already installed:** Skip to "Install whisper" below.

**If PyTorch is NOT installed:** Ask: **"CPU (default) or GPU for voice transcription?"**
- **1. CPU (default)** — lighter install (~1-2 GB), no NVIDIA drivers needed
- **2. GPU** — heavier (~5+ GB), only if you have an NVIDIA GPU and want faster transcription

#### CPU Install (default)

Mode A/B:
```bash
source $PROJECT_ROOT/.venv/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install openai-whisper
```

Mode C:
```bash
pip install --break-system-packages torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install --break-system-packages openai-whisper
```

#### GPU Install

Mode A/B:
```bash
source $PROJECT_ROOT/.venv/bin/activate
pip install openai-whisper
```

Mode C:
```bash
pip install --break-system-packages openai-whisper
```

#### After either install, set environment:

```bash
echo 'export OC_WHISPER_MODEL=base.en' >> ~/.bashrc
echo 'export OC_WHISPER_DEVICE=cpu' >> ~/.bashrc
export OC_WHISPER_MODEL=base.en
export OC_WHISPER_DEVICE=cpu
```

For GPU users, change `cpu` to `cuda` in both lines above.

#### Verify whisper

```bash
which ffmpeg && which whisper && echo "OK" || echo "MISSING — check ffmpeg and whisper installation"
```

---

## Phase 5: Initialize Data and HTTPS

### 5.1: Create data directories

```bash
mkdir -p $PROJECT_ROOT/data/{uploads,sessions,logs}
```

### 5.2: Ask for host URL

Detect the local IP:
```bash
python3 -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()"
```

Store the result as `DETECTED_IP`.

Ask: **"How will you access the chat?"**

Present numbered options:
1. **Network IP** — `http://DETECTED_IP:PORT` (access from other devices on your network)
2. **Localhost** — `http://localhost:PORT` (this machine only)
3. **Custom** — enter a domain or IP (e.g., `https://chat.example.com`)

Wait for the user to reply with 1, 2, 3, or a custom URL.

- **1** → use `http://DETECTED_IP:PORT` as `HOST_URL`
- **2** → use `http://localhost:PORT` as `HOST_URL`
- **3** or a domain/URL → use what they provide as `HOST_URL`

Store as `HOST_URL` — saved in `data/clawedback.json`, used for file share links generated by `file_manager.py`.

Set it in the environment for the current session:
```bash
export OC_HOST_URL="$HOST_URL"
```

### 5.3: Ask about HTTPS

Ask: **"Do you want HTTPS?"**

**If no** (default): Set `SERVER_CMD` to:
- Mode A/B: `cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && source $PROJECT_ROOT/.venv/bin/activate && python main.py`
- Mode C: `cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python3 main.py`

**If yes** — ask how:
- **"I already have certificates"** — ask for full paths to cert and key. Set `SERVER_CMD` to include `--public <cert_path> --private <key_path>`
- **"Get a free certificate with Let's Encrypt"** (Mode B/C only) — run `/oc-ssl` now. It will set up certbot, get the cert, and provide the paths. Then set `SERVER_CMD` accordingly.
- **"I'll set up SSL later"** — use HTTP for now. Tell them to run `/oc-ssl` anytime.

### 5.3: Firewall reminder (Mode B/C)

If running as root on a server, remind:

```bash
# Check if ufw is active
ufw status 2>/dev/null | head -1
```

If ufw is active, suggest:
> Your firewall is active. You may need to open the port:
> ```
> ufw allow 8080/tcp
> ```
> (Or port 443 if using HTTPS on standard port)

---

## Phase 6: Start the Server

```bash
# Kill any leftover server process first
pkill -f "python3 main.py" 2>/dev/null || true
sleep 1

nohup $SERVER_CMD > $PROJECT_ROOT/data/logs/server.log 2>&1 &

# Save the actual server PID (not the nohup wrapper)
sleep 2 && pgrep -f "python3 main.py" | tail -1 > $PROJECT_ROOT/data/server.pid
```

**Verify it started:**

```bash
kill -0 $(cat $PROJECT_ROOT/data/server.pid) 2>/dev/null && echo "Process alive" || echo "PROCESS DIED"
```

And health check:
```bash
curl -sk http://localhost:${OC_PORT:-8080}/api/health
```

(Use `https` if SSL was configured.)

**If the process died or health check failed:** **STOP.** Show the log:
```bash
tail -30 $PROJECT_ROOT/data/logs/server.log
```
Help debug the issue before continuing.

### 6.1: Show the auth token

```bash
cat $PROJECT_ROOT/data/.auth_token
```

Tell the user their token and the URL to access the chat.

---

## Phase 7: Initialize Session State

Write these files with actual content (don't just say "write them"):

**`data/sessions/conversation.json`:**
```bash
cat > $PROJECT_ROOT/data/sessions/conversation.json << 'JSONEOF'
{
  "last_updated": 0,
  "message_count": 0,
  "summary": "",
  "recent_messages": [],
  "user_preferences": {},
  "active_tasks": [],
  "pending_approvals": []
}
JSONEOF
```

**`data/sessions/poll_state.json`:**
```bash
cat > $PROJECT_ROOT/data/sessions/poll_state.json << 'JSONEOF'
{
  "mode": "idle",
  "last_activity": 0.0,
  "cron_job_id": null
}
JSONEOF
```

**`data/sessions/automations.json`:**
```bash
cat > $PROJECT_ROOT/data/sessions/automations.json << 'JSONEOF'
{
  "automations": []
}
JSONEOF
```

**`data/sessions/channels.json`:**
```bash
cat > $PROJECT_ROOT/data/sessions/channels.json << 'JSONEOF'
{
  "channels": [
    {
      "name": "web",
      "type": "builtin",
      "status": "active",
      "config": {"port": 8080}
    }
  ]
}
JSONEOF
```

**`data/sessions/install_mode.json`** (ALL modes):
```bash
cat > $PROJECT_ROOT/data/sessions/install_mode.json << JSONEOF
{
  "mode": "MODE_LETTER",
  "user": "USERNAME_OR_CURRENT_USER",
  "project_root": "$PROJECT_ROOT",
  "installed_at": "$(date -Iseconds)"
}
JSONEOF
```

Replace `MODE_LETTER` with `a`, `b`, or `c`. Replace `USERNAME_OR_CURRENT_USER` with the non-root username (Mode B/C) or `$(whoami)` (Mode A).

---

## Phase 8: Start Polling

This is the critical step — actually call the CronCreate tool:

```
CronCreate with cron "*/1 * * * *" and prompt "/oc-poll"
```

**Verify it was created** by calling CronList.

If CronCreate fails for any reason, tell the user polling won't work automatically and they'll need to run `/oc-poll` manually or restart setup.

---

## Phase 9: Update CLAUDE.md (Mode B/C)

### Mode B — append to CLAUDE.md:

```markdown

### Root Mode
You are running as **root**. You have full system access.
- To run commands as the regular user: `sudo -u USERNAME <command>`
- The project files are owned by root — if the user needs access: `chown -R USERNAME:USERNAME PROJECT_ROOT`
- You can install system packages, manage services, modify system configs
- Still ask before destructive operations (this is not --dangerously-skip-permissions mode)
```

### Mode C — append to CLAUDE.md:

```markdown

### System Install — Full Root Access
You are running as **root** with `--dangerously-skip-permissions`. You have **unrestricted system access** with no confirmation prompts.
- You CAN and SHOULD execute commands directly without asking for permission
- To run commands as the regular user: `sudo -u USERNAME <command>`
- System Python is used directly (no venv) — packages are installed globally
- You can install/remove packages, manage systemd services, modify any file, configure networking, etc.
- This system is designated for ClawedBack use — act accordingly
- IS_SANDBOX=1 is set in the environment
```

Replace `USERNAME` and `PROJECT_ROOT` with actual values.

---

## Phase 10: Post-Setup Summary

Show the complete summary based on mode:

```
clawed-back is ready! (Mode MODE_NAME)

Server: PROTOCOL://localhost:PORT
Auth token: TOKEN
Polling: CronCreate every 1 minute (escalates to 10s when active)
Install mode: MODE_DESCRIPTION
Voice: ENABLED/DISABLED (MODEL on DEVICE)
SSL: ENABLED/DISABLED

To start chatting, open the URL above and enter your auth token.
```

Then show the **future startup command**:

**Mode A:**
```
To restart ClawedBack:
  tmux new -s clawedback
  cd PROJECT_ROOT && claude
  (polling starts automatically via CronCreate)

Reattach: tmux attach -t clawedback
Detach:   Ctrl+B, then D
```

**Mode B:**
```
To restart ClawedBack:
  tmux new -s clawedback
  cd PROJECT_ROOT && sudo -E "$(command -v claude || echo ~/.local/bin/claude)"
  (polling starts automatically via CronCreate)

Reattach: tmux attach -t clawedback
Detach:   Ctrl+B, then D
```

**Mode C:**
```
To restart ClawedBack:
  tmux new -s clawedback
  cd PROJECT_ROOT && sudo -E "$(command -v claude || echo ~/.local/bin/claude)" --dangerously-skip-permissions
  (polling starts automatically via CronCreate)

Reattach: tmux attach -t clawedback
Detach:   Ctrl+B, then D
```

Replace `PROJECT_ROOT` with the actual absolute path.

Also tell the user: **"Next time you restart Claude, just run `/oc-resume` — it will start the server and polling automatically."**

### Save summary to `setup_complete.md`

Write the entire summary (everything shown to the user above — mode, server URL, token, polling, voice, SSL, restart commands) to `$PROJECT_ROOT/setup_complete.md` so the user can reference it later without needing Claude running.

---

## Phase 11: Write Config File

**Only write this AFTER everything above succeeded.** This is the master config that `/oc-resume` reads on future restarts. If setup failed, this file shouldn't exist — that signals to oc-resume to auto-detect instead.

Write `data/clawedback.json` with all the resolved values from this setup session:

```bash
cat > $PROJECT_ROOT/data/clawedback.json << JSONEOF
{
  "mode": "MODE_LETTER",
  "project_root": "$PROJECT_ROOT",
  "username": "USERNAME",
  "host_url": "HOST_URL",
  "python": "PYTHON_PATH",
  "claude_bin": "CLAUDE_BIN_PATH",
  "port": ${OC_PORT:-8080},
  "ssl": {
    "enabled": SSL_BOOL,
    "cert": "CERT_PATH_OR_EMPTY",
    "key": "KEY_PATH_OR_EMPTY"
  },
  "whisper": {
    "installed": WHISPER_BOOL,
    "model": "${OC_WHISPER_MODEL:-turbo}",
    "device": "${OC_WHISPER_DEVICE:-auto}"
  },
  "server_cmd": "THE_FULL_SERVER_START_COMMAND",
  "resume_cmd": "THE_FULL_TMUX_RESUME_COMMAND",
  "configured_at": "$(date -Iseconds)"
}
JSONEOF
```

Values:
- `MODE_LETTER`: `a`, `b`, or `c`
- `USERNAME`: non-root username (Mode B/C) or current user (Mode A)
- `PYTHON_PATH`: `$PROJECT_ROOT/.venv/bin/python` (A/B) or `python3` (C)
- `CLAUDE_BIN_PATH`: result of `command -v claude` or the resolved path
- `SSL_BOOL`: `true` or `false`
- `CERT_PATH_OR_EMPTY` / `KEY_PATH_OR_EMPTY`: cert paths or `""`
- `WHISPER_BOOL`: `true` or `false`
- `SERVER_CMD`: the exact command used to start the server in Step 6
- `RESUME_CMD`: the exact tmux command for future restarts

---

## Error Recovery

If setup fails at any phase:
1. Note which phase failed and why
2. Fix the underlying issue
3. Re-run `/oc-setup` — it should detect what's already done (venv exists, server running, etc.) and skip completed steps
4. For a clean restart: `rm -rf $PROJECT_ROOT/.venv $PROJECT_ROOT/data` and re-run
