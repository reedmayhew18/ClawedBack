<div align="center">

# 🦀 ClawedBack 🦀

### Your Personal AI Assistant — Runs in [Claude Code](https://claude.ai/code)

[![Runs in Claude Code](https://img.shields.io/badge/Runs%20in-Claude%20Code-blueviolet?style=for-the-badge)](https://claude.ai/code)
[![Port of OpenClaw](https://img.shields.io/badge/Port%20of-OpenClaw-ff6b35?style=for-the-badge)](https://github.com/openclaw/openclaw)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue?style=for-the-badge)](LICENSE)

[![Skills](https://img.shields.io/badge/Skills-17%20custom-0078D4?style=flat-square)](.claude/skills)
[![Tool Compat](https://img.shields.io/badge/OpenClaw%20Tools-19%2F23%20matched-2ea44f?style=flat-square)](.claude/skills/oc-hub/references/tool-mapping.md)
[![ClawHub](https://img.shields.io/badge/ClawHub-Compatible-E86C00?style=flat-square)](https://clawhub.ai)
[![Security Scan](https://img.shields.io/badge/Imports-Security%20Scanned-critical?style=flat-square)](.claude/skills/oc-hub)
[![Install Modes](https://img.shields.io/badge/Install-3%20Modes-ff69b4?style=flat-square)](#-setup)

**A clean-room port of [OpenClaw](https://github.com/openclaw/openclaw) that runs inside [Claude Code](https://claude.ai/code)**
**17 skills · 5 agents · 3 install modes · ClawHub compatible**

Multi-channel AI assistant with web chat, file sharing, voice messages, scheduled tasks,<br>
webhook ingestion, approval workflows, and a skill marketplace — all running inside Claude Code.<br>
**Clone, setup, chat.** 🦀

</div>

---

## 🦀 What Is This?

ClawedBack is a **clean-room reimplementation** of the [OpenClaw](https://github.com/openclaw/openclaw) personal AI assistant platform, rebuilt from the ground up to run **inside [Claude Code](https://claude.ai/code)**.

> **Important:** ClawedBack is a **port**, not a fork. It resembles OpenClaw in spirit and functionality — a multi-channel, self-hosted AI assistant with tool execution, automation, and approval workflows — but is an entirely separate codebase with a different architecture. No OpenClaw code was used. 🦀

Where OpenClaw is a TypeScript monolith with a WebSocket gateway, ClawedBack flips the script: **Claude Code IS the agent runtime.** It's [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code/skills).

## 🦀 Setup

Use of this project is subject to [Anthropic's Terms of Service](https://www.anthropic.com/legal/consumer-terms).

### Prerequisites
- Python 3.11+
- tmux (`sudo apt install tmux`)

### Step 1: Install Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

### Step 2: Clone and enter the project

```bash
git clone https://github.com/reedmayhew18/ClawedBack.git
cd ClawedBack
```

### Step 3: Start in tmux

```bash
tmux new -s clawedback
```

### Step 4: Choose your install mode and launch Claude

<details>
<summary><strong>🦀 Mode A: Portable — User (Recommended)</strong></summary>

Best for trying it out, development, or personal use. Safest option.

```bash
claude
# then: /oc-setup → choose Mode A
```

- Python venv inside the project folder
- Runs as your normal user
- Claude asks permission before risky operations (add `--dangerously-skip-permissions` to allow autonomous functionality)

</details>

<details>
<summary><strong>🦀 Mode B: Portable — Root</strong></summary>

Best for a dedicated server or VM where the assistant needs elevated access.

```bash
sudo -E "$(command -v claude || echo ~/.local/bin/claude)"
# then: /oc-setup → choose Mode B
```

- Python venv inside the project folder (same as A)
- Runs as root for full system access
- Commands for the regular user: `sudo -u <username> <command>`
- Still asks permission before destructive operations (add `--dangerously-skip-permissions` for autonomous mode — run the `IS_SANDBOX=1` lines from Mode C first if using this flag)

</details>

<details>
<summary><strong>🦀 Mode C: System Install — Full Root, No Guardrails</strong></summary>

Best for **sandboxes, VMs, or containers designated for ClawedBack**. Not for machines with important data. 🦀

```bash
# Set sandbox flag (both user and root)
echo 'export IS_SANDBOX=1' >> ~/.bashrc && source ~/.bashrc
sudo bash -c 'echo "export IS_SANDBOX=1" >> /root/.bashrc'

# Start Claude as root with no permission prompts
sudo -E "$(command -v claude || echo ~/.local/bin/claude)" --dangerously-skip-permissions
# then: /oc-setup → choose Mode C
```

- System Python directly (`--break-system-packages`), no venv
- Root with `--dangerously-skip-permissions` — Claude can do **anything** without asking
- Maximum capability, zero guardrails

> **WARNING**: Only use Mode C on a system that is fully backed up, sandboxed, or designated for this purpose. Claude will have unrestricted root access with no confirmation prompts.

</details>

### Step 5: Run the setup wizard

```
/oc-setup
```

The wizard handles everything: installs dependencies, starts the server, generates your auth token, offers voice (Whisper) setup, and begins polling. Open the URL it gives you, paste the token, and start chatting. 🦀

**To detach tmux** (keeps ClawedBack running): `Ctrl+B`, then `D`
**To reattach later**: `tmux attach -t clawedback`

<details>
<summary><strong>Restarting After a Reboot</strong></summary>

If the tmux session died (reboot, crash, etc.), start a new one and resume:

```bash
tmux new -s clawedback
cd /path/to/ClawedBack
claude    # (or sudo -E ... for root modes)
```

Then run:
```
/start
```

This ensures the server is up, creates the polling cron job, and runs one poll cycle. Run `/start` whenever you restart Claude Code. 🦀

If the config file is missing (deleted or corrupted), use `/oc-resume` instead — it auto-detects and rebuilds the config.

</details>

<details>
<summary><strong>Updating ClawedBack</strong></summary>

To pull the latest updates from GitHub:
```
/oc-update
```

This fetches upstream changes, shows what's new, and applies them — preserving your `data/`, auth token, config, and any custom skills you've installed. If server files changed, it automatically restarts the server. 🦀

</details>

---

## 🦀 Features

### ✅ Implemented
- 🌐 **Web chat interface** — dark theme, mobile-responsive, full markdown rendering
- 📎 **File uploads** — drag-and-drop, analyze any file type
- 📁 **Organized file system** — date-based storage with temporary share links
- 🎤 **Voice messages** — recorded in-browser, transcribed with Whisper (CPU or GPU)
- 🔐 **Token auth** — auto-generated or custom, single-user security
- 🗄️ **Message queue** — SQLite with WAL mode, CLI interface for skills
- 📡 **SSE streaming** — fetch-based with auth header, cross-device sync
- ✅ **Read receipts** — green checkmark when Claude reads your message
- 🔒 **SSL/HTTPS** — `--ssl` flag, custom cert paths, or free Let's Encrypt via `/oc-ssl`
- 🤖 **17 custom skills** — routing, sessions, approvals, automation, webhooks, file sharing, updates
- ⏰ **Scheduled tasks** — reminders, recurring jobs, cron expressions
- 🔗 **Webhook ingestion** — receive events from GitHub, CI, custom services
- ✋ **Approval gates** — single gates and multi-step workflow chains with crash recovery
- 🧩 **Skill marketplace** — browse ClawHub, import with security scanning
- 🔍 **Security scanning** — mandatory audit of imported skills (subagent-isolated, 5-category scan)
- 📺 **Channel registry** — extensible adapter system for future platforms
- 🔄 **Self-updating** — `/oc-update` pulls latest while preserving config/data
- 🩺 **Self-healing resume** — `/oc-resume` auto-detects setup if config is missing
- 🖥️ **Three install modes** — user, root, or full root with no guardrails

### 🔮 Planned
- 🦀 Browser automation (Playwright)
- 🦀 Device nodes (remote command execution)
- 🦀 TTS voice responses

---

## 🦀 Tool Compatibility (19/23 Matched)

OpenClaw has 23 built-in tools. Claude Code matches **19 of them** out of the box — and the 4 missing are all API wrappers that can be built as skills. Full mapping in [`.claude/skills/oc-hub/references/tool-mapping.md`](.claude/skills/oc-hub/references/tool-mapping.md). 🦀

| Status | Count | Tools |
|--------|-------|-------|
| ✅ **Direct match** | 13 | exec→Bash, read→Read, write→Write, edit→Edit, apply_patch→Edit, web_search→WebSearch, web_fetch→WebFetch, cron→CronCreate, subagents→Agent, agents_list→TaskList, image analyze→Read, +Grep, +Glob |
| 🔧 **Close match** | 6 | code_execution→Bash+venv, browser→Playwright, message→oc-respond, agent send→Agent+`claude -p`, session_status→TaskGet, tts→edge-tts |
| ❌ **Missing** | 4 | x_search (needs xAI API), image_generate (needs DALL-E), video_generate (niche), canvas (OpenClaw-specific) |

**Claude Code actually has tools OpenClaw doesn't**: dedicated `Grep` (ripgrep-powered), `Glob` (fast pattern matching), multimodal `Read` (images, PDFs, notebooks), and typed sub-agents with model selection. 🦀

---

## 🦀 How It Works

```
🌐 Web UI  →  🐍 FastAPI Server  →  🗄️ SQLite Queue  →  🦀 Claude Code  →  💬 Response
```

1. **You chat** through a web interface (text, files, or voice 🎤)
2. **Python catches it** — FastAPI server queues your message in SQLite
3. **Claude Code polls** — hybrid polling checks the queue (1min idle / 10s active)
4. **Claude thinks** — full Claude Code capabilities: tools, web search, code execution, file ops
5. **Response flows back** — through the queue, via SSE, into your browser

### 🦀 Hybrid Polling (The Clever Bit)

Instead of burning tokens polling an empty queue every 10 seconds, ClawedBack uses a two-speed approach:

| State | Method | Interval | Cost |
|-------|--------|----------|------|
| 😴 Idle | CronCreate | 1 minute | Minimal |
| 💬 Active | /loop | 10 seconds | Higher, but responsive |

When you send a message, polling **escalates** to 10s. After 5 minutes of silence, it **de-escalates** back to 1min. This keeps resource and token usage minimal while maintaining responsive functionality. 🦀

## 🦀 Architecture

### Skills-First Design

Everything that involves **reasoning** is a Claude Code skill. Python handles only **persistent I/O**.

| Layer | What | Why Not a Skill? |
|-------|------|-----------------|
| 🐍 Python | Web server, SQLite queue, Whisper | Needs persistent sockets/processes |
| 🦀 Skills | Routing, sessions, tools, approvals, automation | Claude does this natively |
| 🤖 Agents | Code review, debugging, research | Specialized subagent delegation |

### Custom Skills

| Skill | Purpose |
|-------|---------|
| `oc-poll` | 🦀 Hybrid polling controller (the heartbeat) |
| `oc-router` | 🦀 Message routing and intent dispatch |
| `oc-session` | 🦀 Conversation state management |
| `oc-respond` | 🦀 Response formatting and queue delivery |
| `oc-approve` | 🦀 Approval gate for dangerous operations |
| `oc-tools` | 🦀 Tool execution coordinator |
| `oc-voice` | 🦀 Voice message processing |
| `oc-automate` | 🦀 Scheduled tasks and reminders |
| `oc-webhook` | 🦀 Incoming webhook handler |
| `oc-channel` | 🦀 Channel adapter registry |
| `oc-hub` | 🦀 Skill marketplace with security scanning |
| `oc-files` | 🦀 File storage and temporary share links |
| `oc-setup` | 🦀 First-run setup wizard |
| `oc-resume` | 🦀 Self-healing restart |
| `oc-update` | 🦀 Safe upstream updates |
| `oc-ssl` | 🦀 Let's Encrypt certificate setup |
| `oc-token` | 🦀 Auth token management |

### OpenClaw → ClawedBack Mapping

| OpenClaw Concept | ClawedBack Equivalent |
|-----------------|----------------------|
| Gateway (WebSocket) | FastAPI + SQLite queue |
| Agent Runtime (Pi) | Claude Code itself |
| Channels (23+) | Channel adapter skills (web first) |
| ClawHub (marketplace) | `oc-hub` skill |
| Tools system | Claude Code native tools |
| Approval workflows | `oc-approve` skill |
| Cron/automation | CronCreate + `oc-automate` |
| Sessions | `oc-session` skill + JSON files |
| Voice I/O | Whisper + browser MediaRecorder |
| Device nodes | Planned (via SSH skills) |

## 🦀 How Is This Different From OpenClaw?

| | OpenClaw | ClawedBack |
|-|----------|------------|
| **Architecture** | TypeScript monolith | Claude Code skills — minimal footprint |
| **Runtime** | Custom Pi agent + WebSocket daemon | Claude Code itself — no separate runtime |
| **Resource usage** | Always-on process, persistent connections | Idle polling at 1min, escalates only when active |
| **Dependencies** | Node.js, npm, 23+ channel adapters | Python (lightweight I/O only), everything else is skills |
| **Skills** | ClawHub | Claude Code skills (ClawHub-compatible) |
| **Setup** | `npm install` + config files | `claude` → `/oc-setup` |

**In short:** OpenClaw is a full platform you deploy and run. ClawedBack is a set of Claude Code skills with lightweight I/O — minimal resources, no background daemons, scales down to near-zero when idle. 🦀

## 🦀 ClawHub Skill Compatibility

**OpenClaw and Claude Code skills share the same base format.** Both use the [AgentSkills spec](https://docs.openclaw.ai/tools/skills) — Markdown with YAML frontmatter in a `SKILL.md` file. You can import skills from [ClawHub](https://clawhub.ai) directly into ClawedBack. 🦀

```
/oc-hub import <clawhub-skill-slug-or-url>
```

All imports undergo a **mandatory security scan** (isolated subagent, 5-category audit) before installation. ~25% of ClawHub skills contain call-home behavior — ClawedBack catches and optionally remediates these before they touch your system.

| Field | Action |
|-------|--------|
| `name`, `description` | Kept as-is |
| `user-invocable`, `disable-model-invocation` | Kept as-is |
| Markdown body (instructions) | Kept as-is — it's the same format |
| `metadata.openclaw` (OS gating, binary reqs, installers) | Stripped (not applicable in Claude Code) |
| `command-dispatch`, `command-tool` | Stripped (OpenClaw-specific dispatch) |
| `allowed-tools` | Added — inferred from the skill's instructions |

## 🦀 Project Structure

```
clawed-back/
├── 🦀 .claude/skills/         # The brain
│   ├── oc-*/                  # OpenClaw-style functions
│   └── (toolkit skills)       # wizard, tdd, code-review, etc.
│
├── 🤖 .claude/agents/         # Specialist subagents
├── 📋 CLAUDE.md               # Project config
└── 📋 post_install.md         # First-run guide
```

## 🦀 Contributing

If you want to help:

1. **Try it out** and report issues
2. **Build a channel adapter** (Telegram, Discord, Slack)
3. **Create skills** for the marketplace
4. **Improve the web UI**

## 🦀 Disclaimer

All interactions with Claude Code are human-initiated. Recurring tasks use Claude Code's built-in scheduling features (`CronCreate`, `/loop`). This project is not affiliated with, endorsed by, or sponsored by Anthropic.

## 🦀 Credits

- **[OpenClaw](https://github.com/openclaw/openclaw)** — the original inspiration
- **[Whisper](https://github.com/openai/whisper)** — voice transcription

## 🦀 License

AGPL-3.0

---

*Powered by crabs.* 🦀🦀🦀

For questions or concerns, please contact rm28-legal@pm.me
