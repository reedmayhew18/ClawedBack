---
name: oc-automate
description: "Create, list, and manage scheduled tasks and automations. Use when the user asks to schedule something, set a reminder, create a recurring task, or manage existing automations. Trigger phrases: 'remind me', 'every hour', 'schedule', 'at 9am', 'recurring', 'automate', 'cron'."
allowed-tools: "Read Write Bash(python*)"
---

# Automation Manager

Create and manage scheduled tasks for the clawed-back assistant.

## Capabilities

- **Reminders**: "remind me at 3pm to check the deploy"
- **Recurring tasks**: "every morning at 9, summarize my git log"
- **Periodic checks**: "check this URL every hour and tell me if it goes down"
- **Scheduled actions**: "at midnight, run the backup script"

## How It Works

### Creating a Task

When the user requests automation, use CronCreate:

```
CronCreate with cron "<expression>" and prompt "<what to do>"
```

**Examples:**
- "remind me in 1 hour" → one-shot, `recurring: false`, pin to specific time
- "every weekday at 9am" → `cron: "3 9 * * 1-5"`, `recurring: true`
- "every 5 minutes check the queue" → `cron: "*/5 * * * *"`, `recurring: true`

### Tracking Automations

Store all created automations in `data/sessions/automations.json`:

```json
{
  "automations": [
    {
      "id": "cron_abc123",
      "description": "Daily git summary at 9am",
      "cron": "3 9 * * 1-5",
      "prompt": "Summarize all commits from the last 24 hours and send the summary to the chat",
      "recurring": true,
      "created": 1700000000.0
    }
  ]
}
```

### Listing Tasks

When the user asks "what's scheduled?" or "list automations":
1. Read `data/sessions/automations.json`
2. Format as a clean list with description, schedule, and status

### Canceling Tasks

When the user wants to cancel:
1. Find the automation by description or ID
2. Use CronDelete with the job ID
3. Remove from `data/sessions/automations.json`

## Automation Prompt Pattern

When a scheduled task fires, it should:
1. Execute the requested action
2. Send results to the chat queue via `queue_manager.py write`
3. This way the user sees automated results in their chat

Template for automated prompts:
```
Check for [condition]. If found, send results to the chat:
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py write '{"content": "[results]", "type": "text", "metadata": {"source": "automation", "task": "[description]"}}'
```

## Important

- CronCreate jobs are session-scoped — they expire after 7 days and die when the session ends
- Tell the user about the 7-day limit for recurring jobs
- For one-shot reminders, use `recurring: false`
- Avoid :00 and :30 minute marks to prevent API congestion — nudge a few minutes off
- Always confirm what you created: "Scheduled: [description] at [time]. It will [what happens]."
