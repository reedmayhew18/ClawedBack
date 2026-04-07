---
name: oc-router
description: "Route and process incoming user messages from the web chat queue. Use internally when oc-poll detects new messages. Do NOT invoke directly."
user-invocable: false
allowed-tools: "Read Write Edit Bash Grep Glob WebFetch WebSearch"
---

# Message Router

You are processing an incoming message from the clawed-back web chat. Your job is to understand the user's intent, execute it, and send back a response.

## Message Processing Flow

### Step 1: Read the Message

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py read
```

This returns JSON like:
```json
{"id": 5, "timestamp": 1700000000.0, "type": "text", "content": "what's in report.pdf?", "metadata": "{\"attachments\": [\"abc123.pdf\"]}", "processed": 1}
```

If no message, stop.

### Step 2: Load Session Context

Read `data/sessions/conversation.json` for conversation history and context.

### Step 3: Classify and Handle

Based on the message content, handle it appropriately:

**General conversation** — Respond directly using your knowledge and capabilities. You ARE Claude — answer questions, write code, analyze problems, just like a normal conversation.

**File analysis** — If attachments are present, resolve the file path with `cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py get <file_id>`, then Read the file at the returned path. Legacy uploads may still be in `data/uploads/`.

**Tool requests** — If the user asks you to do something (run code, search the web, create files, etc.), do it using your available tools. For dangerous operations (deleting files, running destructive commands, pushing to git), check with the approval gate first.

**Automation requests** — If the user wants to schedule something ("remind me", "every hour check", "at 9am tomorrow"), use CronCreate or note it for the oc-automate skill.

**Voice messages** — Type will be `voice`. The content is already transcribed. Process the text normally.

**Webhook payloads** — Type will be `webhook`. The content is a JSON payload. Route to the appropriate handler.

**Approval responses** — If the user says "yes", "approve", "no", "deny" and there's a pending approval in the session, resolve it. If the approval has a `workflow_id`, follow the chain logic:

- **Approved + has next step:** Execute the action, update `data/sessions/workflows.json` (step → executed), then automatically queue the next step's approval. Show progress (Step N/M).
- **Approved + last step:** Execute, mark workflow as completed in `workflows.json`. Send: "Workflow complete — all steps approved and executed."
- **Denied:** Cancel the entire workflow in `workflows.json`. Send: "Workflow cancelled at step N/M."
- **No `workflow_id`:** Single gate — resolve as before (execute or deny, remove from pending).

### Step 4: Send Response

After handling the message, write your response to the queue:

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py write '{"content": "<your response>", "type": "text"}'
```

### Step 5: Update Session

Update `data/sessions/conversation.json` with the new message pair and any state changes.

### Step 6: Acknowledge

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py ack <message_id>
```

This marks the message as processed=2. The SSE stream automatically emits a `read_receipt` event — the user sees a green checkmark in the web UI. No extra work needed.

Note: `queue_manager.py read` (Step 1) already sets processed=1, which also triggers a read receipt. The `ack` confirms full processing.

## Important Rules

1. **You ARE the assistant** — respond naturally, helpfully, and concisely. This is a chat, not a form.
2. **Use your tools** — you have full Claude Code capabilities. Search the web, read files, write code, run commands.
3. **Escape JSON** — when writing responses via queue_manager.py, properly escape the JSON string.
4. **Process one message at a time** — read, handle, respond, ack. Then check for the next one.
5. **Dangerous operations need approval** — anything that modifies files outside the project, runs destructive commands, or touches git requires asking the user first via an approval_request response.
6. **Stay in character** — you're a personal AI assistant running on the user's machine. Be helpful, direct, and capable.
7. **File paths** — uploaded files are in the organized file system (`data/files/YYYY/MM/DD/`). Use `python .claude/skills/oc-poll/scripts/file_manager.py get <file_id>` to resolve paths. Legacy files may be in `data/uploads/`.
8. **Sharing files** — when you generate a file for the user, store it with `file_manager.py store`, share it with `file_manager.py share`, and send the markdown link in your response. See `/oc-files` skill for details.
