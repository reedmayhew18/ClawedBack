---
name: oc-poll
description: "Check the message queue for new user messages and process them. This is the heartbeat of clawed-back. Typically triggered by CronCreate on a schedule."
allowed-tools: "Bash(python*) Read Write"
---

# Hybrid Polling Controller

You are the heartbeat of clawed-back. Your job is to check if there are new messages from the user and process them.

## Quick Check

First, do a lightweight peek at the queue:

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py peek
```

If `{"pending": 0}` — no new messages. Do nothing more.

If pending > 0 — process messages by reading and handling them:

1. Read the message: `cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py read`
2. Load session context from `data/sessions/conversation.json`
3. Process the message — understand the user's intent and respond using your full capabilities
4. Write your response: `cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py write '{"content": "...", "type": "text"}'`
5. Update the session file with the new message pair
6. Acknowledge: `cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py ack <id>`
7. Check for more: `cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py peek` — if more pending, repeat

## Hybrid Polling State

The polling state file is at `data/sessions/poll_state.json`:

```json
{
  "mode": "idle",
  "last_activity": 0.0,
  "cron_job_id": null
}
```

### State Transitions

**IDLE → ACTIVE**: When you find a message, update `last_activity` to now and `mode` to `active`. The outer polling mechanism should switch from CronCreate (1 min) to /loop (10s).

**ACTIVE → IDLE**: When checking and finding no messages, look at `last_activity`. If it was more than 5 minutes ago, update `mode` to `idle`. The outer mechanism switches back to CronCreate.

## Important

- The peek command is **cheap** — it just counts rows in SQLite. No AI tokens wasted on empty checks.
- Always process ALL pending messages before returning, not just one.
- Keep responses natural and helpful — you're a personal AI assistant.
- If whisper transcription produced garbage, ask the user to repeat.
