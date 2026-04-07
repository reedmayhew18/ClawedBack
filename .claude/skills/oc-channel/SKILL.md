---
name: oc-channel
description: "Manage communication channel adapters (web chat, Telegram, Discord, etc.). Use when the user wants to add a new channel, list channels, or configure channel settings. Trigger phrases: 'add channel', 'connect telegram', 'connect discord', 'list channels'."
allowed-tools: "Read Write Bash(python*)"
---

# Channel Registry

Manages communication channel adapters for clawed-back. Channels are how the assistant communicates with the outside world.

## Current Channels

### Web Chat (Built-in)
- **Status**: Always active
- **Server**: FastAPI at `http://localhost:<port>`
- **Features**: Text, file uploads, voice messages, SSE responses
- **Config**: `server/config.py`

## Channel Registry

Channels are tracked in `data/sessions/channels.json`:

```json
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
```

## Adding a New Channel

To add a channel adapter, you need:

1. **Python adapter** in `server/channels/<name>.py` implementing:
   - `receive()` — get incoming messages and write to queue
   - `send(content)` — deliver outgoing messages to the platform
   - `health_check()` — verify connection is alive

2. **Registration** in `data/sessions/channels.json`

3. **Integration** with the FastAPI server (add routes or background tasks)

## Future Channel Templates

When the user asks to add a channel, guide them through setup:

### Telegram
- Create bot via @BotFather
- Get bot token
- Create `server/channels/telegram.py` using python-telegram-bot or grammY equivalent
- Register webhook or use polling

### Discord
- Create bot in Discord Developer Portal
- Get bot token
- Create `server/channels/discord.py` using discord.py
- Add to server with appropriate permissions

### Slack
- Create Slack app
- Get bot token and signing secret
- Create `server/channels/slack.py` using slack-bolt
- Configure event subscriptions

### Email (IMAP/SMTP)
- Configure IMAP for receiving
- Configure SMTP for sending
- Create `server/channels/email.py`
- Poll IMAP on schedule

## Channel Message Format

All channels must normalize messages to the universal format before queuing:

```json
{
  "type": "text|voice|file|webhook",
  "content": "the message text",
  "metadata": {
    "channel": "telegram",
    "sender": "user123",
    "original_format": {}
  }
}
```

This ensures all skills work regardless of which channel the message came from.

## Listing Channels

When the user asks, read `data/sessions/channels.json` and format:

```
Active channels:
- web (built-in) — http://localhost:8080
- telegram — @my_bot (polling)
```
