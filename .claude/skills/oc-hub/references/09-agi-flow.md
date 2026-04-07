# The AGI Flow: Native Workflow Orchestration in Claude Code

How to connect isolated skills into a coherent system with shared context, a learning loop, self-maintenance, and workflow chaining — using only native Claude Code capabilities.

---

## Table of Contents

1. [What Is the AGI Flow?](#1-what-is-agi-flow)
2. [The Five Layers](#2-the-five-layers)
3. [Minimal Setup (5 Minutes)](#3-minimal-setup)
4. [Full Implementation Guide](#4-full-implementation-guide)
5. [The Learning Loop in Practice](#5-the-learning-loop)
6. [Workflow Chaining](#6-workflow-chaining)
7. [Hook Recipes](#7-hook-recipes)
8. [How Existing Skills Fit the Pattern](#8-existing-skills)

---

## 1. What Is the AGI Flow?

An operating system doesn't do your work — it manages what does. It allocates resources, schedules processes, and gives running programs access to shared state.

An AGI Flow does the same thing for AI skills and agents:

- **Routes tasks** to the right skill or agent
- **Manages shared context** (brand voice, project conventions, domain knowledge)
- **Orchestrates multi-step workflows** across skills
- **Captures feedback** and uses it to improve future sessions
- **Maintains itself** through hooks, health checks, and recovery patterns

This is different from a static automation chain. A Zapier workflow follows a fixed path. An AGI Flow reasons about what to do next based on intermediate results. It handles ambiguity, branches on content, and adapts when things go wrong.

The core insight for Claude Code: **state lives in files, not conversation**. Every layer of the AGI Flow persists through markdown files in predictable locations. This means the system survives context compaction, session restarts, and even complete context resets.

---

## 2. The Five Layers

### Layer 1: Shared Context
**What:** Centralized knowledge that all skills and agents draw from.
**Where:** CLAUDE.md, `.claude/shared-context/`, `.claude/rules/`, `reference/`
**Why:** Without shared context, different skills produce inconsistent output. One writes formally, another casually. One invents features, another contradicts the docs. Shared context is the single source of truth.

**Components:**
- `CLAUDE.md` — project-wide rules, tech stack, conventions (loaded every session)
- `.claude/shared-context/` — brand voice, audience personas, domain glossary (loaded on demand)
- `.claude/rules/` — path-specific rules that load when touching matching files
- `reference/` — deep knowledge guides Claude consults when needed

### Layer 2: Learning Loop
**What:** System improves from session to session based on what worked and what didn't.
**Where:** `.claude/memory/LEARNINGS.md`, `.claude/memory/DECISIONS.md`, `PROGRESS.md`
**Why:** Without learning, every session starts from zero. The same mistakes recur. The same good patterns get rediscovered. The learning loop means each session teaches the next.

**Components:**
- `/wrap-up` skill — captures accomplishments, patterns, anti-patterns, and decisions at end of session
- `LEARNINGS.md` — append-only log of what works and what doesn't
- `DECISIONS.md` — append-only record of decisions with rationale
- `PROGRESS.md` — current state that hands off to the next session

### Layer 3: Self-Maintenance
**What:** The system keeps itself healthy without manual intervention.
**Where:** `.claude/settings.json` hooks, `/context-doctor` skill
**Why:** APIs fail. Context fills up. Destructive commands slip through. A production system handles these gracefully.

**Components:**
- `PreToolUse` hooks — block destructive commands before they execute
- `PostToolUse` hooks — auto-format code after edits
- `SessionStart` hooks — load recent context after compaction
- `Stop` hooks — prompt for session wrap-up
- `/context-doctor` — diagnose and fix context issues on demand

### Layer 4: Workflow Orchestration
**What:** Chain multiple skills into reliable, repeatable pipelines.
**Where:** `.claude/workflows/`, `/workflow` skill, `orchestrator` agent
**Why:** Real work is multi-step. Research → Plan → Write → Review → Publish. Without orchestration, you babysit every transition manually.

**Components:**
- `/workflow define` — create named workflow definitions
- `/workflow run` — execute workflows with state tracking and checkpoints
- `.claude/workflows/<name>.md` — workflow definition files
- `.claude/workflows/<name>-state.md` — execution state (survives compaction)
- `orchestrator` agent — coordinates multi-agent workflows

### Layer 5: Automated Feedback
**What:** Deterministic checks that run without AI reasoning tokens.
**Where:** Hooks in `.claude/settings.json`
**Why:** CLAUDE.md instructions are followed ~70% of the time. Hooks enforce rules at 100%. They're the safety net beneath the AI reasoning layer.

**Components:**
- Safety hooks (block dangerous commands)
- Quality hooks (check output against rules)
- Notification hooks (alert when attention needed)
- Anti-rationalization hooks (catch premature "task complete" declarations)

---

## 3. Minimal Setup (5 Minutes)

The smallest useful AGI Flow has three parts:

### Step 1: Create a conventions file (2 min)
```bash
mkdir -p .claude/shared-context
```
Write `.claude/shared-context/conventions.md` with 10-15 key facts about your project: what it does, who it's for, tech stack, naming conventions, hard rules.

Add to CLAUDE.md:
```markdown
## Shared Context
Read `.claude/shared-context/conventions.md` before making decisions about project direction or conventions.
```

### Step 2: Use /wrap-up at session end (2 min)
Run `/wrap-up quick` before closing. Takes 2 minutes. Captures what you did and what's next. Future sessions start with context instead of from scratch.

### Step 3: Add one hook (1 min)
Add to `.claude/settings.json`:
```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "echo 'Session ending. Run /wrap-up to capture learnings.'"
      }]
    }]
  }
}
```

That's it. You now have shared context, a learning loop, and a self-maintenance reminder. Everything else is additive.

---

## 4. Full Implementation Guide

### Setting up shared context
Run `/skill-store install shared-context`, then `/shared-context full`. The guided interview builds your brand voice profile, audience personas, and domain conventions. All stored in `.claude/shared-context/` and wired into your skills.

### Defining workflows
```
/workflow define content-pipeline
```
Walk through defining steps, inputs/outputs, and checkpoints. The result is a reusable `.claude/workflows/content-pipeline.md` file.

Run it anytime:
```
/workflow run content-pipeline TOPIC="Claude Code best practices"
```

### Configuring hooks
Run `/skill-store install hooks-setup`, then `/hooks-setup all`. Interactive guide configures auto-format, safety, compaction recovery, and session hooks. Merges safely into existing settings.

### The session rhythm
1. **Start** — Claude loads CLAUDE.md, shared context, PROGRESS.md (via SessionStart hook)
2. **Work** — use skills, agents, workflows as needed
3. **Track** — `/progress-tracker save` at natural milestones
4. **Wrap** — `/wrap-up` at end captures learnings
5. **Next session** — starts with everything the previous session learned

---

## 5. The Learning Loop in Practice

### How LEARNINGS.md evolves

**After session 1:**
```markdown
## Session 2026-03-23
### Patterns That Work
- Using /grill-me lightly before /wizard saves rework
### Anti-Patterns Found
- Starting implementation without running tests first caused 3 regressions
```

**After session 5:**
The file has 50 lines. Claude reads it at session start and avoids known anti-patterns automatically. You notice fewer corrections needed.

**After session 20:**
The file has 200 lines. Time to prune. Keep the 30 most impactful learnings, archive the rest. The system is now tuned to your specific project.

### How DECISIONS.md saves hours

Without it: "Why did we choose Postgres over SQLite?" requires rethinking the decision from scratch.

With it:
```markdown
## 2026-03-15 — Database: PostgreSQL over SQLite
- **Decision**: Use PostgreSQL
- **Reason**: Need concurrent writes from multiple workers; SQLite locks on write
- **Alternatives rejected**: SQLite (write locking), MySQL (team has no experience)
- **Impact**: Requires Docker for local dev, need connection pooling in production
```

Future sessions reference this instead of re-debating. Saves 30 minutes per occurrence.

---

## 6. Workflow Chaining

### Workflow definition format
```markdown
# Workflow: feature-pipeline

## Steps
1. **plan** — /grill-me lightly on the feature requirements
   - Output: PLAN.md
   - Checkpoint: true

2. **spec** — /plan-and-spec based on PLAN.md
   - Input: PLAN.md
   - Output: SPEC.md
   - Checkpoint: true

3. **implement** — /wizard to implement the spec
   - Input: SPEC.md
   - Output: (code changes)
   - Checkpoint: false

4. **review** — @code-reviewer on the changes
   - Output: REVIEW.md
   - Checkpoint: true

5. **ship** — /git-workflow commit + pr
   - Input: REVIEW.md (for PR description)
   - Checkpoint: true
```

### State tracking
Each workflow run creates a state file:
```markdown
# State: feature-pipeline (run 2026-03-23)
- Step 1 plan: COMPLETED — output: PLAN.md
- Step 2 spec: COMPLETED — output: SPEC.md
- Step 3 implement: IN_PROGRESS
- Step 4 review: PENDING
- Step 5 ship: PENDING
```

If context resets mid-workflow: `/workflow resume feature-pipeline` reads the state file and continues from step 3.

---

## 7. Hook Recipes

### Python project
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{"type": "command", "command": "ruff format \"$CLAUDE_FILE_PATHS\" 2>/dev/null; ruff check --fix \"$CLAUDE_FILE_PATHS\" 2>/dev/null"}]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'pip install.*--break-system-packages'; then echo 'Use a virtual environment instead' >&2; exit 2; fi"}]
    }]
  }
}
```

### TypeScript project
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{"type": "command", "command": "prettier --write \"$CLAUDE_FILE_PATHS\" 2>/dev/null"}]
    }]
  }
}
```

### Session management (any project)
```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "startup|resume",
      "hooks": [{"type": "command", "command": "cat PROGRESS.md 2>/dev/null | head -30"}]
    }],
    "Stop": [{
      "hooks": [{"type": "command", "command": "echo 'Run /wrap-up to capture session learnings.'"}]
    }]
  }
}
```

---

## 8. How Existing Skills Fit the Pattern

| Existing Skill | AGI Flow Role |
|---|---|
| `/wizard` | Workflow orchestration (8-phase pipeline with built-in verification) |
| `/plan-and-spec` | Workflow orchestration (planning pipeline with forced iteration) |
| `/progress-tracker` | Learning loop (mid-session state persistence) |
| `/wrap-up` | Learning loop (end-of-session knowledge capture) |
| `/context-doctor` | Self-maintenance (diagnose and recover from context issues) |
| `/grill-me` | Shared context (extract project knowledge through interview) |
| `/research` | Shared context (bring external knowledge into the system) |
| `/code-review` | Automated feedback (quality checks via subagent) |
| `/project-optimizer` | Self-maintenance (full project health audit) |
| `orchestrator` agent | Workflow orchestration (multi-agent coordination) |

The AGI Flow isn't a separate system bolted on top. It's the recognition that these skills already form a coherent architecture — they just needed explicit connection points (workflow chaining, learning capture, hook configuration) to function as a unified whole.
