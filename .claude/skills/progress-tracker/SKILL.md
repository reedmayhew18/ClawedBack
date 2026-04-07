---
name: progress-tracker
description: Create and update progress/handoff documents for long-running work. Use when nearing context limits, switching tasks, ending a session, or when the user says "save progress", "handoff", "wrap up", or "I need to pick this up later".
argument-hint: "[save/load/update]"
disable-model-invocation: true
allowed-tools: Read, Write, Glob
---

# Progress Tracker

## Goal
Produce or update a PROGRESS.md file in the project root that captures enough state for any future session to resume work without loss. Success = a file exists that answers: what's done, what's in flight, what's next, and what decisions were made.

## Dependencies
**Tools:** Read (load existing PROGRESS.md and source files), Write (save PROGRESS.md), Glob (find relevant files)
**Save location:** `PROGRESS.md` in the project root (same directory as CLAUDE.md)

## Context
On `load`: read PROGRESS.md and any files listed under "In Progress" to restore full awareness before resuming.
On `save`/`update`: read the current PROGRESS.md (if it exists) to merge — do not overwrite completed items.

Maintain external state files that survive context resets, compaction, and session changes.

## Commands

### Save: `/progress-tracker save`
1. Read existing `PROGRESS.md` if it exists (preserve completed items — do not overwrite)
2. Scan conversation history and any open files to reconstruct: what's done, what's in progress, decisions made, known issues, next steps
3. Draft the full PROGRESS.md content using the template below

**CHECKPOINT:** Present the drafted PROGRESS.md to the user. Ask: "Does this capture everything accurately? Should I add, remove, or correct anything before saving?" Do NOT write the file until the user approves.

4. Write the approved content to `PROGRESS.md` in the project root
5. Output: "Saved to PROGRESS.md — [N] completed items, [N] next steps."

Create or update PROGRESS.md with:

```markdown
# Progress - [Date]

## Completed
- [x] Specific task with file paths
- [x] Another completed task

## In Progress
- [ ] Current task and its state
- Files being modified: path/to/file.ts

## Key Decisions Made
- Decision: [what was decided]
  - Reason: [why]
  - Impact: [what this means for other work]

## Known Issues / Landmines
- Issue description with file paths
- Workarounds currently in place

## Next Steps (in order)
1. Specific next action with file paths
2. Second action
3. Third action

## Context for Next Session
- Important state not captured elsewhere
- Relevant file paths and function names
- What you still don't understand (important!)
```

### Load: `/progress-tracker load`
Read PROGRESS.md and any files listed under "In Progress". Summarize the current state to the user.

**CHECKPOINT:** Present the loaded state summary. Ask: "Here's where we left off — does this match your expectations, or has anything changed?" Do NOT resume work until the user confirms.

### Update: `/progress-tracker update`
1. Read existing `PROGRESS.md` — if not found, fall back to `save` flow
2. Identify what has changed since the last save: newly completed items, new decisions, new blockers, revised next steps
3. Draft the updated PROGRESS.md (move completed items to Completed, update In Progress, prepend new next steps)

**CHECKPOINT:** Show a diff-style summary of what changed (e.g., "Marking X complete, adding Y to Next Steps"). Ask: "Looks right?" Do NOT write until confirmed.

4. Write the updated file
5. Output: "PROGRESS.md updated."

## When to Use
- Before `/clear` - save state first
- Before context gets near capacity (check with `/context`)
- At end of work session
- Before switching to a different task
- After completing a major milestone

## Key Principle
Anything important that only exists in conversation will be lost on compaction. If it matters, it goes in a file.
