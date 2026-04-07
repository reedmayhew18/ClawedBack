---
name: oc-session
description: "Load and save conversation session state. Use internally when processing messages to maintain context across the chat. Do NOT invoke directly."
user-invocable: false
allowed-tools: "Read Write Bash(python*)"
---

# Session Manager

Manages conversation state so Claude Code maintains context across messages received through the web chat queue.

## Session File

Session state is stored at: `$PROJECT_ROOT/data/sessions/conversation.json`

## Schema

```json
{
  "last_updated": 1700000000.0,
  "message_count": 42,
  "summary": "User is working on a Python data pipeline. Recently asked about pandas performance.",
  "recent_messages": [
    {"role": "user", "content": "...", "timestamp": 1700000000.0},
    {"role": "assistant", "content": "...", "timestamp": 1700000001.0}
  ],
  "user_preferences": {},
  "active_tasks": [],
  "pending_approvals": []
}
```

## How to Use

### Loading Session

Read `data/sessions/conversation.json`. If it doesn't exist, start fresh.

### Updating Session

After processing each message:

1. Append the user message and your response to `recent_messages`
2. Keep only the last **20 messages** in `recent_messages` (sliding window)
3. Update `summary` if the conversation topic shifted — this summary survives the window
4. Update `last_updated` timestamp
5. Write the file back

### Summary Strategy

The `summary` field is your long-term memory. Update it when:
- The user starts a new topic
- Important context is about to leave the 20-message window
- The user states a preference or correction

Keep the summary under 500 characters. Focus on: what the user is working on, key decisions made, and stated preferences.

### Active Tasks

Track ongoing work the user mentioned:
```json
{"task": "fix the login bug", "status": "in_progress", "created": 1700000000.0}
```

### Pending Approvals

Track operations waiting for user approval:
```json
{"id": "abc123", "action": "bash", "command": "rm -rf old/", "requested": 1700000000.0}
```

For workflow chain approvals, the object also includes `workflow_id`, `workflow_name`, `step`, and `total_steps`. See `/oc-approve` for details.

### Active Workflows

Multi-step approval chains are tracked in a separate file: `data/sessions/workflows.json`. This file persists across crashes and restarts. See `/oc-approve` for the full schema and lifecycle. The session's `pending_approvals` list handles individual step approvals; `workflows.json` tracks the overall chain state.
