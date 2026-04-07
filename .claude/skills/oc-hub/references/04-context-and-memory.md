# Context and Memory Management for Claude Code

The definitive guide to CLAUDE.md, context window management, compaction, progressive disclosure, and persistent project memory.

---

## Table of Contents

1. [CLAUDE.md Best Practices](#claudemd-best-practices)
2. [Context Window Management](#context-window-management)
3. [Compaction: How It Works and Strategies](#compaction-how-it-works-and-strategies)
4. [Progressive Disclosure](#progressive-disclosure)
5. [Memory System and Persistent State](#memory-system-and-persistent-state)
6. [Spec-Driven Modeling](#spec-driven-modeling)
7. [Project Structure Patterns](#project-structure-patterns)

---

## CLAUDE.md Best Practices

### What CLAUDE.md Is For

CLAUDE.md is the only file that loads into every single Claude Code conversation by default. It is the mechanism for onboarding Claude into your codebase at the start of each session. Since Claude has no memory of previous sessions and no knowledge of your codebase beyond what you provide, CLAUDE.md is the highest-leverage point in the entire workflow.

Use CLAUDE.md to define three things:

- **WHAT**: The tech stack, project structure, and codebase map. Especially critical in monorepos — tell Claude what the apps are, what the shared packages are, and what each is for so it knows where to look.
- **WHY**: The purpose of the project and the function of its different parts.
- **HOW**: How Claude should work on the project. What commands to run, how to verify changes, how to run tests, typechecks, and compilation.

### The System Reminder Behavior

Claude Code injects CLAUDE.md into the context with a `<system-reminder>` wrapper:

```
<system-reminder>
IMPORTANT: this context may or may not be relevant to your tasks.
You should not respond to this context unless it is highly relevant to your task.
</system-reminder>
```

This means Claude will actively ignore CLAUDE.md content it deems irrelevant to the current task. The more instructions you include that are not universally applicable, the more likely Claude ignores all of them — including the ones that matter.

### The Instruction-Following Decay Problem

Frontier thinking LLMs can follow approximately 150-200 instructions with reasonable consistency. Key research findings:

- Smaller models degrade exponentially with instruction count; frontier models degrade linearly.
- Claude Code's own system prompt contains approximately 50 individual instructions — already a third of a frontier model's reliable instruction budget before your CLAUDE.md adds anything.
- As instruction count increases, instruction-following quality decreases **uniformly**. Adding more instructions does not cause the model to ignore only the new ones; it begins ignoring all instructions more consistently.
- LLMs bias toward instructions at the **peripheries** of the prompt: the very beginning (system prompt and CLAUDE.md) and the very end (most-recent user messages).

**Practical implication**: Keep CLAUDE.md under 200 lines, ideally under 60 lines, with fewer than 30 instructions.

### What to Include

**Include in CLAUDE.md:**

1. A single-line project description
2. Core development commands Claude cannot guess (custom scripts, non-standard tooling, e.g., `bun` instead of `node`)
3. Project structure overview — especially for monorepos
4. Non-negotiable constraints stated with hard language: "Never" and "Always" (soft language like "prefer" and "try to" gets compressed away under pressure)
5. Mistakes and edge cases that have tripped Claude up in previous sessions
6. Required environment variables
7. Branch naming conventions and PR rules
8. How to run tests, lint, and typecheck
9. Pointers to detailed reference files (not the content itself)

**Do NOT include in CLAUDE.md:**

- Standard language conventions Claude already knows
- Generic advice like "write clean code"
- File-by-file descriptions of things Claude can discover by reading the codebase
- Long explanations, tutorials, or detailed API documentation
- Code style guidelines — use a linter instead (LLMs are far slower and more expensive than `ruff`, `biome`, or `eslint`)
- Task-specific instructions that are irrelevant to most work (e.g., how to structure a new database schema, if that's not what you do every day)

### Claude Is Not a Linter

Never use CLAUDE.md to enforce code style. LLMs are comparably expensive and slow compared to traditional linters and formatters. Style guidelines bloat your context window and eat up the instruction budget.

Instead:
- Set up formatters and linters to run automatically (Biome, Ruff, ESLint)
- Create a Claude Code Stop hook that runs your formatter and presents errors to Claude for fixing
- Create a slash command that points Claude at `git status` or `git diff` for code review

### Do Not Auto-Generate CLAUDE.md

Both Claude Code (`/init`) and other tools offer auto-generation. Do not use it. CLAUDE.md affects every phase of your workflow and every artifact produced. A bad line of CLAUDE.md has the potential to create bad implementations across the entire project. Spend time crafting it deliberately — every single line.

### CLAUDE.md Annotated Template

```markdown
# [Project Name]

[One sentence description of what the project does and why it exists.]

## Tech Stack
- Language/runtime: [e.g., Python 3.11+, Node 20, Rust stable]
- Framework: [e.g., FastAPI, Next.js App Router]
- Database: [e.g., PostgreSQL with pgvector]
- Package manager: [e.g., uv, bun, cargo]

## Project Structure
[Brief monorepo map or key directory descriptions — 3-8 lines max]

## Development Commands
```bash
# Start dev server
[command]

# Run tests
[command]

# Lint and format
[command]

# Typecheck
[command]
```

## Non-Negotiables
- NEVER [critical constraint #1]
- NEVER [critical constraint #2]
- ALWAYS [critical requirement #1]

## Common Mistakes to Avoid
- [Specific gotcha from experience #1]
- [Specific gotcha from experience #2]

## Reference Docs
For task-specific guidance, read the relevant file before starting:
- agent_docs/building.md — build system details
- agent_docs/testing.md — test patterns and fixtures
- agent_docs/api-design.md — API conventions
- agent_docs/database.md — schema and migration patterns
```

### Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
|---|---|---|
| Auto-generated with `/init` | Generates verbose, poorly targeted instructions | Write manually |
| 500+ line CLAUDE.md | Instruction decay makes all rules unreliable | Target under 200 lines |
| Code style guidelines | Wastes instruction budget; use a linter | Configure `biome` or `ruff` |
| Every possible command | Bloats context; Claude ignores rarely relevant info | Include only essential commands |
| Soft constraints ("try to", "prefer") | Get compressed away under context pressure | Use "NEVER" and "ALWAYS" |
| Importing large files globally with `@` | Expands into context at session start, consuming tokens | Use progressive disclosure instead |

---

## Context Window Management

### Why Context Degrades

As a conversation grows, the model's context window fills. Older instructions get compressed or dropped to make room for recent content. This causes observable drift:

- Claude switches from a convention it was following perfectly an hour ago
- Ignores naming conventions, language preferences, or format rules
- Starts adding boilerplate it was told to avoid
- Makes unsolicited "improvements" to code outside the task scope

This is not a bug — it is a fundamental property of how LLMs handle context. The solution is to externalize state to files rather than relying on conversation memory.

### The U-Shaped Attention Problem

Models attend well to content at the very beginning and end of the context window, but lose track of content in the middle. This means:

- Instructions at the start of the session (CLAUDE.md, early messages) receive good attention
- The most-recent user messages receive good attention
- Everything in the middle degrades — including decisions made 50 turns ago

A 1M token context window does not solve this; it just moves the middle further out. Structured external memory scales better than raw context length.

### Performance Degradation Thresholds

Community research and tool analysis shows consistent patterns:

- **~100k tokens**: Performance begins to noticeably drop
- **~150k tokens**: Dramatic performance degradation
- **~200k tokens (Claude Code default limit)**: Auto-compaction triggers at ~95% capacity
- **Recommended manual compaction**: At 60-80% capacity, before auto-compaction fires

The Codex CLI sets default auto-compact thresholds at approximately 180k-244k tokens depending on model, with a 95% effective context window safety margin. Community consensus is that 95% is too late — triggering compaction yourself at 85% or earlier produces better summaries.

### The Four Core Strategies

**Priority order: implement all four, they compound.**

#### 1. CLAUDE.md as Persistent Memory

CLAUDE.md survives `/clear` and context compaction. It is re-injected at the start of every session and after every reset. Your critical constraints — the rules that, if violated, break your project — belong here. Everything else belongs elsewhere.

Use hard language for actual invariants:
```
# Never Do
# Never add console.log to production code
# Never modify files in src/legacy/
# Never use `any` as a TypeScript type

# Always Do
# Always add JSDoc to exported functions
# Always run the lint script after Python or TypeScript changes
```

#### 2. `/clear` Between Tasks

Use `/clear` at natural milestones: after a feature is complete, after tests pass, after a significant refactor, when switching to a different module.

`/clear` wipes conversation history but CLAUDE.md survives. Constraints persist; accumulated cruft does not.

Recommended rhythm: `implement → test → /clear → implement next feature`

Do not let a single session grow large enough to require compaction. If a task is so large that it requires compaction, the task is too large — break it into smaller pieces.

#### 3. Multi-Agent Isolation

For complex projects, use Claude Code's Task tool to spawn sub-agents. Each sub-agent gets a fresh 200k context window.

```
Main Agent (orchestrator)
├── Sub-agent A: Implement auth module (fresh context)
├── Sub-agent B: Write tests (fresh context)
└── Sub-agent C: Update documentation (fresh context)
```

Benefits:
- No cross-contamination between agents
- Parallel execution
- Each agent reads CLAUDE.md independently — constraints stay consistent
- The orchestrator stays clean; workers do the token-heavy research

Note: Sub-agents return concise summaries to the orchestrator, so 12 agents can consume 85% of the parent context depending on reporting verbosity.

#### 4. `/compact` for Mid-Task Recovery

When you cannot `/clear` (you need conversation history), use `/compact`. It summarizes the conversation into a compressed form, freeing context space while preserving key information.

Use when:
- You are mid-task and cannot reset
- Context is clearly getting full (responses becoming vague or drifting)
- You need to continue a complex thread

**Risk**: `/compact` loses detail. Specific error messages, exact line numbers, and nuanced decisions may not survive compression. Use it as a recovery mechanism, not a routine tool.

**Pro tip**: Trigger `/compact` manually before Claude auto-compacts. You can add custom instructions:
```
/compact - preserve the current implementation plan and all file paths discussed
```

### Comparison Matrix

| Method | Effect | Cost | Best For |
|---|---|---|---|
| CLAUDE.md | Prevents drift entirely | One-time setup | All projects |
| `/clear` | Full reset | Lose conversation | Between tasks |
| Multi-agent | Complete isolation | More complex setup | Parallel/large work |
| `/compact` | Partial reset | Detail loss | Mid-task recovery |
| External files | Persistent state | Upfront discipline | Long projects |

---

## Compaction: How It Works and Strategies

### What Compaction Does

Compaction takes the entire conversation history, uses an LLM to generate a structured summary, then starts a new session with the summary as the only context. The detailed tool results, exploration history, and back-and-forth is discarded; the summary replaces it.

Key distinction:
- `/compact` — summarizes and continues; preserves the session
- `/clear` — wipes everything; CLAUDE.md reloads but conversation is gone

### Claude Code's Auto-Compaction

Claude Code's built-in auto-compaction triggers at approximately 95% context capacity. Community consensus is this triggers too late. By the time it fires, crucial mid-conversation context is already degraded.

The compaction prompt Claude uses (extracted from community research):

```
Your task is to create a detailed summary of the conversation so far,
paying close attention to the user's explicit requests and your previous
actions. This summary will be used as context when continuing the
conversation, so preserve critical information including:

## What was accomplished
## Current work in progress
## Files involved
## Next steps
## Key user requests or constraints
```

### Cross-Platform Compaction Comparison

Research on how major coding assistants implement compaction (source: GitHub Gist by badlogic):

**Claude Code**
- Manual: `/compact [optional custom instructions]`
- Auto: ~95% context capacity
- Quality degrades with multiple compactions (cumulative information loss)
- Model can "go off the rails" if auto-compact fires mid-task

**OpenAI Codex CLI**
- Manual: `/compact`
- Auto: Token-based threshold (`model_auto_compact_token_limit`) — ~180k-244k tokens depending on model
- Preserves the last ~20k tokens of recent user messages alongside the summary
- Has retry logic with exponential backoff for failed compactions
- Warns: "Long conversations and multiple compactions can cause the model to be less accurate"

Codex compaction prompt:
```
You are performing a CONTEXT CHECKPOINT COMPACTION. Create a handoff
summary for another LLM that will resume the task.

Include:
## Current progress and key decisions made
## Important context, constraints, or user preferences
## What remains to be done (clear next steps)
## Any critical data, examples, or references needed to continue

Be concise, structured, and focused on helping the next LLM seamlessly
continue the work.
```

**OpenCode (sst/opencode)**
- Manual: `/compact`
- Auto: When `isOverflow()` is true — when tokens exceed `(context_limit - output_limit)`
- Has separate "prune" mechanism: scans backward through tool calls, protects last 40k tokens of tool output (`PRUNE_PROTECT`), prunes tool outputs beyond threshold if >20k tokens are prunable (`PRUNE_MINIMUM`)
- Auto-compaction can be disabled via `OPENCODE_DISABLE_AUTOCOMPACT` environment variable

**Amp (Sourcegraph)**
- Philosophy: "For best results, keep conversations short and focused"
- No automatic compaction
- Manual "Handoff" feature: specify a goal for the next task, Amp analyzes the current thread and extracts relevant information into a new message for a fresh thread
- Also offers: Fork (duplicate context at a specific point), Thread References (reference other threads to extract information on-demand)
- Uses a secondary model to extract relevant information during handoff

### SDK-Level Compaction (Anthropic Python SDK)

For programmatic workflows, the Anthropic Python SDK (>=0.74.1) supports automatic compaction via `compaction_control`:

```python
runner = client.beta.messages.tool_runner(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    tools=tools,
    messages=messages,
    compaction_control={
        "enabled": True,
        "context_token_threshold": 50000,   # tokens before triggering
        "model": "claude-haiku-4-5",        # cheaper model for summaries (optional)
        "summary_prompt": "...",            # custom prompt (optional)
    },
)
```

**How it works under the hood:**
1. After each turn, the SDK checks if token usage exceeds `context_token_threshold`
2. When exceeded: injects a summary request as a user turn
3. Claude generates a summary wrapped in `<summary></summary>` tags
4. The SDK clears conversation history and replaces it with only the summary
5. Processing resumes with the compressed context

**Measured token savings** (customer service ticket processing, 5 tickets, 35 tool calls):

| Metric | Baseline (no compaction) | With Compaction |
|---|---|---|
| Input tokens | 204,416 | 82,171 |
| Output tokens | 4,422 | 4,275 |
| Total tokens | 208,838 | 86,446 |
| Compactions | N/A | 2 |
| **Savings** | — | **122,392 tokens (58.6%)** |

Without compaction, input tokens grew linearly to 204k for just 5 tickets. With compaction, the context reset twice and total input stayed bounded at 82k.

### Threshold Guidelines

| Range | Use Case |
|---|---|
| 5k–20k tokens | Iterative task processing with clear per-item boundaries (ticket queues, document batches) |
| 50k–100k tokens | Multi-phase workflows with larger natural checkpoints |
| 100k–150k tokens | Tasks requiring substantial historical context; fewer compactions, more detail preserved |
| 100k (default) | Good balance for general long-running tasks |

Do not set the threshold too low — if it is lower than the summary itself will generate, you create a compaction loop.

### Custom Summary Prompt Template

The best compaction prompts are structured around resumability:

```
Create a detailed summary for continuing this session. Include:

1. **Task Overview**
   - The user's core request and success criteria
   - Any clarifications or constraints specified

2. **Completed Work**
   - What tasks were finished
   - Files modified and their current status
   - Key outputs or artifacts produced

3. **Current State**
   - What is being worked on right now
   - Where exactly the work is in the sequence

4. **Important Discoveries**
   - Technical constraints or requirements uncovered
   - Decisions made and their rationale
   - Errors encountered and how they were resolved
   - Approaches tried that didn't work (and why)

5. **Next Steps**
   - Specific actions needed to complete the task
   - Blockers or open questions to resolve
   - Priority order if multiple steps remain

6. **Context to Preserve**
   - User preferences or style requirements
   - Domain-specific details that aren't obvious
   - Key file paths, line numbers, and variable names

Be concise but complete — err toward including information that would
prevent duplicate work or repeated mistakes.
```

### Key Design Decisions

- **Threshold**: 85-90% is better than the default 95% (Claude Code) — manual compaction at 60-80% produces the best summaries
- **Pruning**: Consider pruning old tool outputs before full compaction (OpenCode approach) to reduce noise in the summary
- **Warn users**: Notify when compaction has occurred and that quality may degrade with multiple compactions
- **Disable option**: Allow disabling auto-compaction for tasks that require full context
- **Custom instructions**: Support `/compact [instructions]` for targeted summaries that emphasize what matters for the current task
- **Session continuity**: The summary should feel like a seamless continuation, not a restart

---

## Progressive Disclosure

### The Core Principle

Progressive disclosure means Claude only loads detailed reference files when it specifically needs them, not at the start of every session. This protects the context window from bloat while making information available on demand.

There are two mechanisms:

1. **Explicit file pointers in CLAUDE.md** — Claude reads the pointer list and decides which files to load before starting a task
2. **Path-scoped rules** — Rules that only load when Claude is working with matching files

### Organizing Reference Files

Instead of putting all documentation in CLAUDE.md, keep task-specific instructions in separate markdown files with self-descriptive names:

```
agent_docs/
├── building_the_project.md
├── running_tests.md
├── code_conventions.md
├── service_architecture.md
├── database_schema.md
├── service_communication_patterns.md
├── api-design.md
└── troubleshooting.md
```

In CLAUDE.md, list these files with a brief description and instruct Claude to decide which are relevant:

```markdown
## Reference Docs
Before starting work, decide which of these files are relevant and read them:
- agent_docs/building_the_project.md — build system, scripts, environment setup
- agent_docs/database_schema.md — schema structure, migration patterns
- agent_docs/api-design.md — REST conventions, request/response patterns
- agent_docs/troubleshooting.md — known errors and their fixes
```

**Prefer pointers to copies.** Do not include code snippets in reference files if the actual source files exist — they will become stale. Include file:line references that point Claude to the authoritative context.

### The `@path/to/import` Syntax

CLAUDE.md supports importing external files directly:

```markdown
@README.md
@package.json
@docs/workflow-guide.md
@~/.personal-preferences.md   # Personal preferences not in version control
```

**Important caveats:**
- Imported files expand fully into the context at session start — they are not loaded on demand
- Recursive imports work up to 5 hops deep
- Relative paths resolve relative to the file containing the import, not the working directory
- Unconditional imports still consume tokens; only use `@` for files that are **always** relevant

For genuinely on-demand loading, use skills or path-scoped rules instead.

### Path-Scoped Rules

Place modular markdown rules in `.claude/rules/` with YAML frontmatter:

```markdown
---
paths: ["src/components/*.tsx"]
---

# React Component Rules
- Use named exports only
- Props interfaces must be defined above the component
- Use React.FC only when children are expected
```

These rules load only when Claude is working with files matching the `paths` glob. This eliminates noise when Claude is working elsewhere in the project.

### Skills vs. CLAUDE.md

| | CLAUDE.md | Skill (skill.md) |
|---|---|---|
| **When loaded** | Start of every session | Only when Claude triggers that specific task |
| **Token cost** | Every request | Only during relevant tasks |
| **Purpose** | Always-on project rules | Expert playbook for one specific workflow |
| **Size** | Under 200 lines | Can be larger; loaded on demand |
| **Example** | "Always use TypeScript" | Detailed API style guide |

**How they work together**: CLAUDE.md contains a lightweight global rule like "always follow our API conventions" while a dedicated skill holds the massive API style guide that Claude only reads when actively building an API.

You can create global skill triggers in CLAUDE.md:
```markdown
Every time you write content, use the humanizer skill.
```

### Context Needs Chart

Inside individual skill files, define a "context needs chart" that maps task steps to required reference documents:

```markdown
## Context Needs
- When determining target audience: load shared/icp.md
- When writing positioning copy: load shared/positioning.md
- When checking brand voice: load shared/tone-profile.md
- Do NOT load any of these files unless the step specifically requires it
```

This tells Claude exactly when to pull each heavy reference document, keeping sessions fast and focused.

---

## Memory System and Persistent State

### The Core Insight

Conversation context is volatile; the filesystem is persistent. Stop relying on Claude to "remember" things across sessions. Instead, externalize project state to files that Claude reads at the start of each continuation.

This means:
- Claude does not need to remember decisions — they are documented
- Context compaction cannot destroy critical information — it lives on disk
- Session restarts are not setbacks — they are normal workflow steps
- Long projects become tractable — there is no effective upper limit

### Recommended File Set

**For any significant project, maintain these files:**

```
PROJECT_SPEC.md       — Requirements, decisions made, and decisions rejected (with reasons)
PROJECT_TASKS.md      — Full task breakdown with dependencies mapped out
PROJECT_STATE.md      — Progress, which files are complete, which attempt you're on
HANDOFF.md            — Current-session handoff document for context transitions
learnings.md          — Accumulated observations about what works and what doesn't
troubleshooting.md    — Real error messages, symptoms, and exact fixes
```

**Domain-specific reference files:**

```
agent_docs/
├── api-design.md
├── database.md
├── python.md
├── typescript.md
└── architecture.md
```

**Shared brand/product context (for content or marketing workflows):**

```
shared/
├── icp.md                      — Ideal customer profile
├── positioning.md              — Market positioning and differentiation
├── tone-profile.md             — Voice and style guidelines
└── product-marketing-context.md  — Canonical product details for all marketing tasks
```

### PROJECT_SPEC.md

The most important file for long projects. It captures:

- All requirements and constraints
- Every decision made and why
- Decisions **rejected** and why (prevents re-exploring dead ends)
- Strategic intent (why does this project exist)
- Tactical scope (what is included and excluded)
- Operational details (specific parameters and requirements)

**Do not let Claude guess at requirements.** Before any work starts, run a comprehensive discovery phase: Claude asks questions about requirements, constraints, and success criteria. Every interpretation gets confirmed, not assumed. This front-loads work but ensures PROJECT_SPEC.md captures the real requirements.

### HANDOFF.md and the Handoff Pattern

When context fills up or you need to start a fresh session, generate a handoff document before clearing:

```
Before ending this session, generate a HANDOFF.md with:
- Current work in progress (exact file, function, line if applicable)
- Completed work this session
- Open decisions not yet resolved
- Specific traps and dead ends to avoid
- Relevant file paths with brief descriptions
- Next action to take in the new session
```

In the new session:
```
Read HANDOFF.md and continue from where the previous session left off.
```

This eliminates conversation bloat while preserving continuity. The next Claude reads the full document — not a summary of a summary — and continues exactly where work stopped.

### learnings.md and the Retrospective Pattern

Create a wrap-up skill (e.g., `/retrospective`) that runs at the end of each session:

1. Claude reviews the entire conversation transcript — commands run, errors encountered, fixes applied
2. Extracts actionable insights and appends them to `learnings.md`
3. Documents what worked, what failed, and why
4. Flags patterns (e.g., "articles that open with a direct answer rank better")

**Document failures especially.** The most valuable learnings.md entries are failure paths: "I tried X and it broke because Y." These prevent Claude from wasting tokens re-exploring known dead ends.

**Close the loop**: Ensure that active skills and CLAUDE.md instruct Claude to read `learnings.md` before starting related tasks. This creates a self-improving feedback loop.

**Prune regularly**: Blindly appending every session creates bloat. Periodically review `learnings.md` and remove redundant or outdated entries.

**Automate with a SessionEnd hook**:

```json
// .claude/settings.json
{
  "hooks": {
    "SessionEnd": "/retrospective"
  }
}
```

### troubleshooting.md

Maintain a troubleshooting file with:
- Real error messages (not paraphrased — exact text)
- Actual symptoms (what you observed)
- Exact fixes that worked
- Environment conditions where the error occurs

When Claude encounters a related error, it reads this file to provide historically accurate solutions instead of guessing from training data.

### Extended Context Protocol (ECP) Pattern

For projects spanning multiple sessions with complex state, structure the workflow explicitly:

**Initialization phase:**
1. Describe the project
2. Claude asks comprehensive discovery questions
3. Claude generates PROJECT_SPEC.md, PROJECT_TASKS.md, PROJECT_STATE.md
4. Claude adds completion markers to each generated file

**Execution phase:**
1. Claude works through tasks
2. Updates PROJECT_STATE.md after each task
3. Logs decisions to PROJECT_SPEC.md

**Context-full branching:**
1. When you see compaction happening, cancel the response
2. Branch back to the checkpoint (right after project initialization)
3. Provide a minimal handoff: `"CONTINUATION - Attempt 2, interrupted file was X, next action is Y"`
4. Claude reads state files and continues

Every file Claude generates gets a completion marker at the end. This allows validation: a Python script can check all files for completion markers and generate a status report from the state files.

The key difference from "starting new chats": nothing gets lost. Rejected options, edge cases, specific phrasings after iteration — all captured in PROJECT_SPEC.md. The next Claude reads the actual documents, not a retrieved snippet or summary.

---

## Spec-Driven Modeling

### What It Is

Spec-driven modeling shifts you away from relying on ephemeral conversational context by establishing a permanent, externalized memory for your project before work begins. A TECHSPEC.md acts as a "research contract" — a durable reference document that survives context compaction and session restarts.

### TECHSPEC.md Structure

```markdown
# Project: [Name]

## Core Objectives and Learnings
[What you are trying to learn or achieve. Not what you will build — what you want to know or prove.]

## Hypotheses
1. [Hypothesis A]
2. [Hypothesis B]
[List the specific hypotheses being tested so Claude understands why each task exists.]

## Success Criteria
- **Best case**: [e.g., 95%+ accuracy under 1M parameters]
- **Realistic case**: [e.g., 80%+ accuracy]
- **Worst case**: [e.g., 60%+ accuracy, still publishable]
[Define upfront to prevent moving the goalposts after seeing initial results.]

## Project Phases
### Phase 1: [Name]
- Tasks: [...]
- Completion criteria: [...]
- Status: [ ] Not started / [x] Complete

### Phase 2: [Name]
...

## Technical Constraints
- [Constraint A, e.g., maximum 1M parameters]
- [Constraint B, e.g., inference must run in under 100ms]

## Parameter Ranges
- [Parameter A]: [min] to [max], step [step]
- [Parameter B]: ...

## Budget and Limits
- Compute budget: [...]
- Time budget: [...]

## Baseline Results
[Updated by Claude as work progresses — marks phases complete, records results]
```

### How to Use TECHSPEC.md

1. **Before writing any code**: distill your research, prior papers, and notes into TECHSPEC.md
2. **Pair with PROJECT_TASKS.md**: the spec defines what and why; the task list defines the atomic steps to get there
3. **Treat as living document**: have Claude actively update it to mark phases complete and record results
4. **Reference in every session**: instruct Claude to read TECHSPEC.md at the start of related sessions

In automated environments, external systems can read the TECHSPEC.md to estimate compute needs and schedule jobs accordingly.

---

## Project Structure Patterns

### Universal Layout

A project structure that supports Claude Code effectively:

```
project-root/
├── CLAUDE.md                    # Session onboarding (keep lean)
├── TECHSPEC.md                  # Project research contract
├── PROJECT_SPEC.md              # Requirements and decisions
├── PROJECT_TASKS.md             # Task breakdown with dependencies
├── PROJECT_STATE.md             # Progress tracking
├── HANDOFF.md                   # Current session handoff doc
│
├── agent_docs/                  # Progressive disclosure reference files
│   ├── building.md
│   ├── testing.md
│   ├── api-design.md
│   ├── database.md
│   ├── architecture.md
│   └── troubleshooting.md
│
├── .claude/
│   ├── settings.json            # Hooks, permissions
│   ├── commands/                # Custom slash commands
│   └── rules/                   # Path-scoped rules (YAML frontmatter)
│       ├── react-components.md  # paths: ["src/components/*.tsx"]
│       ├── api-routes.md        # paths: ["src/api/**/*.ts"]
│       └── migrations.md        # paths: ["db/migrations/**"]
│
├── shared/                      # Centralized brand/product context (if applicable)
│   ├── icp.md
│   ├── positioning.md
│   └── tone-profile.md
│
└── learnings.md                 # Self-improving knowledge base
```

### Monorepo-Specific Guidance

In monorepos, CLAUDE.md is critical for orientation. Without it, Claude will not know where to look for anything.

Include in CLAUDE.md:
- A table or list of each package/app with a one-line description
- Which packages are shared and which are standalone
- How packages depend on each other
- Which commands run at root vs. inside a specific package

**Hindsight monorepo example** (from vectorize-io/hindsight):

```markdown
# Monorepo Structure
- hindsight-api-slim/     Core FastAPI server with memory engine (Python, uv)
- hindsight-control-plane/ Admin UI (Next.js, npm)
- hindsight-cli/          CLI tool (Rust, cargo)
- hindsight-clients/      Generated SDK clients (Python, TypeScript, Rust)
- hindsight-docs/         Documentation site (Docusaurus)

## Key Commands
# Start API server
./scripts/dev/start-api.sh

# Run tests (parallelized)
cd hindsight-api-slim && uv run pytest tests/

# Lint
./scripts/hooks/lint.sh

# Regenerate OpenAPI spec after API changes (REQUIRED)
./scripts/generate-openapi.sh
```

### Reddit Community Strategies (Most Upvoted)

Collected from r/ClaudeAI and r/ClaudeCode discussion threads:

**The CLAUDE.md Method** (most recommended)
Put core architecture, constraints, and the high-level plan in CLAUDE.md. Create additional files like `PLAN.md` or `TODO.md` and instruct Claude in CLAUDE.md to read them at session start.

**Document and Clear**
Implement one feature successfully. Have Claude update `session_summary.md` and `current_task.md`. Save the state. Use `/clear`. Start a new conversation referencing those context files. The accumulation of concise info in context files tightens guardrails the further the project progresses.

**Research / Plan / Build Separation**
- Session 1: Research phase — build a document covering APIs, codebase layout, key file locations, important code sections
- Session 2: Planning phase — read the research document, build the phased plan
- Session 3+: Build phase — execute one phase per session, update documentation, push to version control

**Handoff Pattern**
Before context fills, have Claude create a summary document: progress, key decisions, next steps. Start a new session, have it read that document to get up to speed.

**Subagent Delegation**
Send subagents off to do research or implement smaller pieces. They do the token-heavy work and report back a concise summary, keeping the main orchestrator context clean.

**AI-Format CLAUDE.md**
Keep a human-readable `claude_human.md` and have Claude convert it to a stripped-down AI-optimized `CLAUDE.md`. The AI format removes all human niceties and focuses on facts only. This reduces noise in the context.

**Small Files Discipline**
"How the hell are you using so much context? Break your work down into smaller chunks. And always start fresh context beyond 100-120k."
Keep individual source files small. Large files (50+ function 2k LOC files) are inefficient for both humans and LLMs. SOLID and DRY principles apply.

### Centralized Shared Context

For workflows using multiple skills (content production, research pipelines), create a centralized shared folder rather than duplicating context in each skill:

```
shared-context/
├── icp.md               # Ideal customer profile
├── positioning.md       # Market differentiation
├── tone-profile.md      # Voice and style
├── case-studies.md      # Key examples
└── product-context.md   # Canonical product details
```

Point each skill to this shared folder via its context needs chart. Every new skill you add immediately benefits from this knowledge base. A copywriting skill can pull from `positioning.md` to write a draft, then automatically pass to a humanizer skill that checks against `tone-profile.md`.

**Key benefit**: Single source of truth. Update the ICP once; every skill that references it is immediately updated.

---

## Quick Reference

### Session Startup Checklist

```bash
# New session for ongoing project:
# 1. Claude reads CLAUDE.md automatically
# 2. Reference the handoff or task file:
#    "Read PROJECT_STATE.md and continue where we left off"
# 3. Verify context is loaded:
#    "Summarize the current project state before we begin"
```

### Context Management Decision Tree

```
Is this a new project?
  → Set up CLAUDE.md, PROJECT_SPEC.md, PROJECT_TASKS.md
  → Run discovery questions before any implementation

Is the context getting long (>100k tokens)?
  → /compact with custom instructions preserving key constraints
  → Or: generate HANDOFF.md, /clear, start fresh session reading HANDOFF.md

Is a task too large for one session?
  → Break into phases in PROJECT_TASKS.md
  → Use Document-and-Clear pattern between phases
  → Use subagents for parallel work

Is Claude drifting (ignoring conventions, changing style)?
  → Check: are constraints in CLAUDE.md with hard language?
  → /clear and start a fresh session reading PROJECT_STATE.md
  → Move constraints to "Never/Always" format

Is compaction breaking your workflow?
  → Trigger /compact manually before 80% context fill
  → Provide custom compaction instructions
  → Externalize all state to files before compacting
```

### Compaction Prompt for Manual Use

Run this before context fills to create a handoff:

```
Before we hit context limits, generate a HANDOFF.md file with:
1. What was accomplished in this session (specific files, functions, tests)
2. Current work in progress (exact location in the codebase)
3. Decisions made and why (not just what — the reasoning)
4. Things we tried that didn't work (to avoid re-exploring)
5. Next 3 specific actions to take in the new session
6. File paths that are most relevant to pick up where we left off
```
