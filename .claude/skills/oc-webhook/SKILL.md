---
name: oc-webhook
description: "Handle incoming webhook payloads from external services. Use internally when the router encounters a webhook-type message. Supports GitHub, GitLab, custom webhooks. Do NOT invoke directly."
user-invocable: false
allowed-tools: "Read Write Bash(python*) WebFetch"
---

# Webhook Handler

Processes incoming webhook payloads received by the FastAPI server at `POST /api/webhook/:name`.

## How Webhooks Arrive

External services POST to `http://<server>:<port>/api/webhook/<name>`. The server queues the payload as:

```json
{
  "type": "webhook",
  "content": "{\"action\": \"push\", \"ref\": \"refs/heads/main\", ...}",
  "metadata": "{\"webhook_name\": \"github\"}"
}
```

## Processing

1. Parse the webhook name from metadata
2. Parse the JSON payload from content
3. Match to a registered handler (see below)
4. Execute the handler logic
5. Send a summary to the chat so the user knows what happened

## Registered Handlers

Handlers are defined in `data/sessions/webhooks.json`:

```json
{
  "handlers": [
    {
      "name": "github",
      "description": "GitHub push/PR events",
      "action": "Summarize the event and notify in chat"
    },
    {
      "name": "health",
      "description": "Health check failures",
      "action": "Investigate the failing service and suggest fixes"
    }
  ]
}
```

If no handler matches the webhook name, send a generic notification to the chat with the payload summary.

## Common Webhook Patterns

### GitHub
- **Push**: Summarize commits, check for issues
- **PR opened**: Summarize changes, note review needed
- **CI failure**: Analyze logs, suggest fixes

### Custom Health Checks
- **Service down**: Check status, attempt diagnosis
- **Error spike**: Analyze error patterns

## Response Format

Always notify the user in chat:

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py write '{"content": "**Webhook: github**\n\nPush to main by @user: 3 commits\n- Fix auth bug\n- Update deps\n- Add tests", "type": "text", "metadata": {"source": "webhook", "webhook_name": "github"}}'
```

## Setting Up Webhooks

The user can register webhooks by telling you:
- "Set up a GitHub webhook" → provide the URL `http://<host>:<port>/api/webhook/github`
- "Add a health check webhook" → create handler in webhooks.json, provide URL

The webhook endpoint requires the same auth token as a Bearer header.
