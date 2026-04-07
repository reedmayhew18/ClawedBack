---
name: oc-approve
description: "Approval gate for dangerous operations. Use internally before executing destructive commands, file deletions, git pushes, or external API calls from the web chat. Do NOT invoke directly."
user-invocable: false
allowed-tools: "Read Write Bash(python*)"
---

# Approval Gate

Human-in-the-loop safety gate for dangerous operations requested through the web chat.

## When to Require Approval

Always require approval before:
- Running shell commands that modify or delete files
- Running `git push`, `git reset`, or destructive git operations
- Making external API calls or sending data to third parties
- Installing packages or modifying system state
- Any operation the user didn't explicitly request

## How It Works

### Step 1: Request Approval

Write an approval request to the outgoing queue:

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py write '{
  "content": "I need your approval to run:\n\n```\nrm -rf old_backups/\n```\n\nThis will permanently delete the old_backups directory. Reply **yes** to approve or **no** to deny.",
  "type": "approval_request",
  "metadata": {"action_id": "<unique_id>", "action": "bash", "command": "rm -rf old_backups/"}
}'
```

### Step 2: Record Pending Approval

Add the pending approval to the session file (`data/sessions/conversation.json`):

```json
{
  "pending_approvals": [
    {
      "id": "<unique_id>",
      "action": "bash",
      "command": "rm -rf old_backups/",
      "requested": 1700000000.0,
      "description": "Delete old_backups directory"
    }
  ]
}
```

### Step 3: Wait

Do NOT execute the operation. The next poll cycle will pick up the user's response.

### Step 4: Resolve (handled by oc-router)

When the router sees a "yes"/"approve" or "no"/"deny" message and there's a pending approval:
- **Approved**: Execute the operation, remove from pending, confirm completion
- **Denied**: Remove from pending, acknowledge the denial
- **Expired**: Approvals older than 1 hour are auto-denied

## Pre-Approved Operations (Allowlist)

These operations do NOT require approval:
- Reading files anywhere on the system
- Writing files within `$PROJECT_ROOT/`
- Running Python scripts within `$PROJECT_ROOT/`
- Web searches and web fetches
- Creating/listing cron jobs within the session

## Approval Message Format

Be clear and specific:
- State exactly what will happen
- Show the exact command
- Mention if it's irreversible
- Ask for yes/no

---

## Multi-Step Approval Chains

For tasks that need multiple sequential human approvals (e.g., migrate → test → deploy), use a workflow chain instead of individual gates.

### Creating a Chain

Define all steps upfront, persist them to `data/sessions/workflows.json`, then queue only step 1's approval.

**Step 1: Write the workflow to disk**

```bash
# Read existing workflows (or start fresh)
cat $PROJECT_ROOT/data/sessions/workflows.json 2>/dev/null || echo '{"workflows":{}}'
```

Add the new workflow:
```json
{
  "workflow_id": "<unique-id>",
  "workflow_name": "Human-readable name",
  "total_steps": 3,
  "current_step": 1,
  "status": "in_progress",
  "steps": [
    {"step": 1, "description": "What step 1 does", "action": "bash", "command": "the command", "status": "pending", "approved_at": null, "executed_at": null},
    {"step": 2, "description": "What step 2 does", "action": "bash", "command": "the command", "status": "waiting", "approved_at": null, "executed_at": null},
    {"step": 3, "description": "What step 3 does", "action": "bash", "command": "the command", "status": "waiting", "approved_at": null, "executed_at": null}
  ],
  "created": 1700000000.0,
  "cancelled_at": null,
  "completed_at": null
}
```

Write to `data/sessions/workflows.json`. This file survives crashes and restarts.

**Step 2: Queue the first step's approval**

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py write '{
  "content": "**Workflow: Deploy v2** (Step 1/3)\n\nI need to run database migrations:\n```\npython manage.py migrate\n```\n\nApprove? Reply **yes** to proceed or **no** to cancel the workflow.",
  "type": "approval_request",
  "metadata": {"workflow_id": "<id>", "step": 1, "total_steps": 3}
}'
```

**Step 3: Record in pending_approvals**

Add to session's `pending_approvals` with the workflow fields:
```json
{
  "id": "<id>-step1",
  "workflow_id": "<id>",
  "workflow_name": "Deploy v2",
  "step": 1,
  "total_steps": 3,
  "action": "bash",
  "command": "python manage.py migrate",
  "description": "Run database migrations",
  "requested": 1700000000.0
}
```

### Chain Resolution (handled by oc-router)

When an approval with `workflow_id` is resolved:

**Approved:**
1. Execute the action
2. Update `workflows.json`: current step → `status: "executed"`, set `approved_at` and `executed_at`
3. If there's a next step: set it to `status: "pending"`, increment `current_step`, queue its approval request
4. If it was the last step: set workflow `status: "completed"`, `completed_at` timestamp. Send: "Workflow 'name' complete — all N steps approved and executed."

**Denied:**
1. Do NOT execute
2. Update `workflows.json`: workflow `status: "cancelled"`, `cancelled_at` timestamp
3. Send: "Workflow 'name' cancelled at step N/M."

**Expired (>1 hour):**
1. Same as denied — cancel the entire workflow

### Approval Message Format for Chains

Always show progress:
```
**Workflow: Deploy v2** (Step 2/3)

Step 1 ✅ Run database migrations — completed
Step 2 ➡️ Run full test suite — awaiting approval
Step 3 ⏳ Deploy to production — waiting

I need to run:
```pytest```

Approve? Reply **yes** to proceed or **no** to cancel the workflow.
```

### Single Gates vs Chains

- **No `workflow_id`** → single gate, works exactly as before
- **Has `workflow_id`** → part of a chain, follows the workflow lifecycle above

Both types coexist in `pending_approvals`. They don't interfere with each other.
