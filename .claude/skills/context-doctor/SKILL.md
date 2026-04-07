---
name: context-doctor
description: Diagnose and fix context window issues. Use when Claude seems confused, forgetful, slow, or the user says "context is full", "you forgot", "you're repeating yourself", "start fresh", or "why are you ignoring my instructions".
disable-model-invocation: true
context: fork
allowed-tools: Bash, Read, Write
---

# Context Window Doctor

Diagnose context issues and apply the right fix. Runs in a forked context so the diagnostic itself doesn't pollute the user's session.

## Goal
Identify what's causing the user's context problem, apply a specific fix, and confirm the issue is resolved. Done when the user confirms the fix worked or a HANDOFF.md is written for a clean restart.

## Process

### Step 1: Gather Diagnostics
Ask the user to run `/context` and share the output (this is a slash command only the user can execute). Also check:
- Current conversation length estimate
- Whether CLAUDE.md exists and its line count
- Number of active skills (description budget usage)
- Whether PROGRESS.md or HANDOFF.md exist

### Step 2: Diagnose
Match symptoms to causes:

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Ignores CLAUDE.md rules | CLAUDE.md too long or contradictory | Trim under 200 lines, use emphasis on critical rules |
| Forgets earlier instructions | Context full, compaction dropped details | Write to files (PLAN.md, PROGRESS.md), then `/compact` with focus |
| Repeats itself or circles | Context polluted with failed approaches | After 2 failed corrections, `/clear` with better prompt |
| Slow or degraded responses | Context near capacity (>60% is caution zone) | `/clear` if switching tasks, `/compact` with focus if continuing |
| Unrelated context pollution | Mixed tasks in one session | `/clear` between unrelated tasks |
| Lost progress after compaction | Important state only in conversation | Dump to PROGRESS.md/HANDOFF.md before next compaction |

**CHECKPOINT:** Present the diagnosis to the user: detected symptom, likely cause, and proposed fix. Ask: "Does this match what you're experiencing? Should I apply this fix?"

### Step 3: Apply Fix
Execute the recommended fix. Common actions:
- Write state to PROGRESS.md or HANDOFF.md
- Suggest user run `/compact [focus instructions]` with specific focus
- Suggest user run `/clear` for a fresh start
- Recommend trimming CLAUDE.md if over 200 lines

### Step 4: Verify
After fix is applied, confirm with the user that the issue is resolved.

## Prevention Strategies
Offer these proactively:
1. **Document & Clear**: Dump progress to file → `/clear` → start fresh reading that file
2. **Use subagents**: Delegate verbose ops (test runs, research, log analysis)
3. **One task per session**: `/clear` between unrelated work
4. **External state**: Plans, specs, progress in files (not just conversation)
5. **Proactive compaction**: `/compact [focus]` before auto-compact triggers at ~95%
6. **Lean CLAUDE.md**: Under 200 lines. Progressive disclosure for the rest.

## Output
Brief diagnosis report: symptom identified, cause, fix applied (or recommended for user to apply). For Emergency Reset cases, confirm HANDOFF.md path.

## Emergency Reset
If context is badly polluted:
1. Write current state to HANDOFF.md: progress, decisions, next steps, file paths
2. Tell user to run `/clear`
3. Tell user: start fresh with "Read HANDOFF.md and continue from where we left off"
