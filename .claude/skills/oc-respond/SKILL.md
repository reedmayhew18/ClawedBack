---
name: oc-respond
description: "Write a response to the user via the message queue. Use internally when processing a user message and you need to send the reply back through the web chat. Do NOT use for direct terminal conversations."
user-invocable: false
allowed-tools: "Bash(python*)"
---

# Response Formatter

You are sending a response back to the user through the clawed-back web chat interface.

## How to Send a Response

Run this command with the response content:

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py write '{"content": "<YOUR_RESPONSE>", "type": "text"}'
```

## Rules

1. **Escape JSON properly** — the content goes inside a JSON string, so escape quotes and newlines
2. **Markdown is supported** — the web UI renders the response as-is, so markdown formatting works
3. **One response per message** — if you need to send multiple parts, make multiple calls
4. **Type field** — use `text` for normal responses, `approval_request` for approval gates, `error` for errors
5. **Keep responses focused** — the user is chatting, not reading a report. Be concise.
6. **Real-time delivery** — the SSE stream pushes responses to the browser immediately (1s poll). The user sees your response appear in real-time with no page refresh.
7. **Cross-device** — if the user has multiple browser tabs/devices open, all of them receive the response via SSE. Message deduplication is handled client-side.
8. **File sharing** — to include a downloadable file in your response, use `file_manager.py share` to get a temporary URL, then include it as a markdown link: `[Filename.pdf](http://host:8080/files/uuid.pdf?filename=Filename.pdf)`. See `/oc-files` skill for the full workflow.

## Example

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py write '{"content": "Here is the file summary:\n\n- 3 functions\n- 120 lines\n- No issues found", "type": "text"}'
```

For approval requests:
```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py write '{"content": "I need to run: `rm old_backup/`. Approve? Reply yes/no.", "type": "approval_request", "metadata": {"action": "bash", "command": "rm old_backup/"}}'
```
