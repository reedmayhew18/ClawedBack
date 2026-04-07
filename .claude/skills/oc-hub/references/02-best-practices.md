# Claude Code Best Practices

A single authoritative reference synthesized from Anthropic's official guide, production team reports, and community-tested patterns. Every tip is actionable.

---

## Overview

Claude Code is an agentic coding environment, not a chatbot. It reads your files, runs commands, and autonomously works through problems. This changes how you work: you describe what you want, Claude figures out how to build it.

The single most important resource to manage is the **context window**. Performance degrades as it fills. Most best practices exist to protect that resource and to give Claude clear criteria for verifying its own work.

The difference between productive and unproductive sessions comes down to three things: constrain Claude aggressively before execution, give it a way to verify its output, and manage context deliberately across sessions.

---

## Table of Contents

1. [CLAUDE.md: Project Memory](#1-claudemd-project-memory)
2. [Planning Before Coding](#2-planning-before-coding)
3. [Prompting Effectively](#3-prompting-effectively)
4. [Context Management](#4-context-management)
5. [Hooks as Deterministic Guardrails](#5-hooks-as-deterministic-guardrails)
6. [Test-Driven Development](#6-test-driven-development)
7. [Git Workflows and Safety](#7-git-workflows-and-safety)
8. [Custom Commands, Skills, and Subagents](#8-custom-commands-skills-and-subagents)
9. [Session Workflow Reference](#9-session-workflow-reference)
10. [Model Selection and Cost](#10-model-selection-and-cost)
11. [Automation and CI/CD](#11-automation-and-cicd)
12. [Production-Quality Code Guardrails](#12-production-quality-code-guardrails)
13. [Anti-Patterns to Avoid](#13-anti-patterns-to-avoid)
14. [Quick Reference: Commands and Shortcuts](#14-quick-reference-commands-and-shortcuts)

---

## 1. CLAUDE.md: Project Memory

CLAUDE.md is the highest-leverage configuration in Claude Code. Claude reads it at the start of every session. Without it, Claude guesses at your conventions on every task.

### Run `/init` first

```bash
/init
```

This analyzes your codebase to detect build systems, test frameworks, and patterns. Use the output as a starting point, then refine.

### What to include

From Anthropic's official guide:

| Include | Exclude |
|---|---|
| Bash commands Claude cannot guess (`npm run test`, `./vendor/bin/sail test`) | Anything Claude can infer by reading code |
| Code style rules that differ from language defaults | Standard language conventions |
| Testing instructions and preferred test runners | Detailed API docs (link instead) |
| Repository etiquette (branch naming, PR conventions) | Information that changes frequently |
| Architectural decisions specific to your project | Long explanations or tutorials |
| Developer environment quirks and required env vars | File-by-file codebase descriptions |
| Common gotchas and non-obvious behaviors | Self-evident rules like "write clean code" |

### Example CLAUDE.md structure

```markdown
## Build & Test
- Build: `npm run build`
- Test: `npm test -- --testPathPattern=`
- Lint: `npm run lint`
- Type check: `npm run typecheck`

## Code Style
- TypeScript everywhere, strict mode
- ES modules (import/export), not CommonJS
- Functional components with hooks only
- 2-space indentation, camelCase variables, PascalCase components

## Architecture
- State: Zustand (see src/stores/)
- API calls: custom client in src/utils/api.ts
- New components require a test file alongside them

## Hard Rules
- Never use class components
- Never bypass the error boundary setup
- Never commit directly to main
- Use `drizzle:generate` for migrations, not raw SQL
```

### Size limits and instruction budget

From HumanLayer's analysis of Claude Code internals: frontier models follow roughly 150–200 instructions before compliance drops, and Claude Code's own system prompt consumes about 50 of those slots. That leaves roughly 100–150 slots for your rules.

- Keep the root CLAUDE.md under 150 lines (60–100 lines is ideal)
- Use `.claude/rules/` to split large instruction sets into separate files
- Wrap domain-specific rules in XML-style tags to prevent them from being ignored as the file grows longer

Test adherence by adding a canary line like "always address me as Mr. Tinkleberry" and watching how quickly it disappears from Claude's responses. When the canary vanishes, your instructions are being deprioritized.

### Progressive disclosure with subdirectory files

Keep the root CLAUDE.md general. For domain-specific rules, reference separate files rather than inlining them:

```markdown
## Monorepo root CLAUDE.md
- Python: always use type hints. Test: `pytest -x --tb=short`
- Never use raw SQL, prefer the ORM
- For payment system work, read docs/payment-architecture.md first
- For API conventions, read src/api/CLAUDE.md
```

Claude loads subdirectory CLAUDE.md files automatically when working in those directories. A CLAUDE.md in `src/persistence/` activates only when Claude is working there, keeping the root file clean.

### Import syntax for related files

```markdown
## CLAUDE.md
See @README.md for project overview and @package.json for available commands.

## Git workflow
@docs/git-instructions.md

## Personal overrides
@~/.claude/my-project-instructions.md
```

Do not `@`-import large documentation files into CLAUDE.md. This embeds the entire file on every run, burning your instruction budget before the conversation starts.

### CLAUDE.md placement

- `~/.claude/CLAUDE.md` — applies to all Claude sessions (personal defaults)
- `./CLAUDE.md` — project root, check into git for team sharing
- `./src/api/CLAUDE.md` — subdirectory-specific, loads on demand
- Parent directories in monorepos are loaded automatically up to the project root

Check CLAUDE.md into git. The file compounds in value over time as your team adds hard-won gotchas. If Claude keeps violating a rule, either the file is too long or the rule phrasing is ambiguous — add `IMPORTANT:` or `YOU MUST` to increase adherence, then prune anything that is not actively preventing mistakes.

---

## 2. Planning Before Coding

### The core principle

Planning collapses ambiguous decisions into a reviewed specification. Each decision point where Claude has to guess independently reduces accuracy. If you assume 80% accuracy per decision across 20 decision points, you get 0.8^20 ≈ 1% probability of a fully correct implementation. Planning moves each decision point close to 100% because you have already made the call.

### Four-phase workflow (from Anthropic's official guide)

**Phase 1 — Explore (Plan Mode)**

Press `Shift+Tab` twice to enter Plan Mode. Claude reads files and answers questions without making any changes.

```
read /src/auth and understand how we handle sessions and login.
also look at how we manage environment variables for secrets.
```

**Phase 2 — Plan (still in Plan Mode)**

```
I want to add Google OAuth. What files need to change?
What's the session flow? Create a plan.
```

Press `Ctrl+G` to open the plan in your text editor for direct editing before proceeding.

**Phase 3 — Implement (exit Plan Mode)**

Press `Shift+Tab` once to switch back to Normal Mode.

```
implement the OAuth flow from your plan. write tests for the
callback handler, run the test suite and fix any failures.
```

**Phase 4 — Commit**

```
commit with a descriptive message and open a PR
```

Skip planning for small, well-scoped tasks. If you could describe the diff in one sentence, ask Claude to do it directly.

### The annotation cycle workflow

Community-tested pattern from production teams at Abnormal AI and incident.io:

1. Ask Claude to draft a `plan.md` file
2. Open the file in your editor and add inline notes where Claude made the wrong call: `> NOTE: use drizzle:generate, not raw SQL` or `> NOTE: this should be PATCH, not PUT`
3. Send the annotated plan back with the guard phrase: **"address all notes, don't implement yet"** — without this phrase, Claude skips the plan and starts coding
4. Repeat until the plan has no ambiguity left
5. Tell Claude to implement

```markdown
## plan.md — annotation cycle example

### Step 3: Database migration
Create a new migration for the users table.
> NOTE: use drizzle:generate, not raw SQL
> NOTE: add created_at with default NOW()

### Step 4: API endpoint
Add PUT /users/:id endpoint.
> NOTE: this should be PATCH, not PUT. Partial updates only.
```

### Countering satisficing (the "replan" pattern)

Claude commits to the first workable plan it finds. For high-stakes decisions (architecture, data models, API surfaces), force iterative critique-and-refine loops with the `replan` skill pattern:

1. **Understand and clarify** — read code, state assumptions, ask questions before proposing anything
2. **Initial plan** — a first draft, expected to be imperfect
3. **Critique** — structured self-review: simplicity, maintainability, testability, hand-wavy gaps, unverified API assumptions
4. **Alternatives** — address specific weaknesses found in the critique
5. **Develop best alternative** — flesh it out to the same level of detail as the original
6. **Iterate** — repeat steps 3–5 at least three times, checking in between iterations
7. **Final plan** — cherry-pick the best elements from all iterations

Create `.claude/skills/replan/SKILL.md` with `allowed-tools: Read, Glob, Grep, WebSearch` (no Write or Edit — replan is for thinking, not doing).

Add user checkpoints between iterations. These are where you inject context Claude cannot find in code: product goals, domain constraints, recent team decisions, regulatory requirements.

### Let Claude interview you

For large features, have Claude gather requirements before planning:

```
I want to build [brief description]. Interview me in detail using the AskUserQuestion tool.

Ask about technical implementation, UI/UX, edge cases, concerns, and tradeoffs.
Don't ask obvious questions, dig into the hard parts I might not have considered.

Keep interviewing until we've covered everything, then write a complete spec to SPEC.md.
```

Once the spec is complete, start a fresh session to execute it. The new session has clean context focused entirely on implementation.

### Write specs to external files

Persist plans so they survive context resets:

- `plan.md` — implementation checklist with checkboxes
- `SPEC.md` — full feature specification
- `architecture.md` — high-level system design
- `decisions.md` — record of architectural choices with rationale

One developer spent two hours writing a 12-step spec and estimated it saved 6–10 hours of implementation time.

### Thinking levels

Phrases mapped to increasing reasoning depth:

- `think` — straightforward features or bug fixes
- `think hard` — complex business logic or architectural decisions
- `think harder` — performance optimization, security-sensitive code
- `ultrathink` — legacy integration, complex algorithms, genuinely stuck

Use `ultrathink` sparingly. It increases both time and token cost. For Opus 4.6, use the `/model` effort slider (low/medium/high) or set `CLAUDE_CODE_EFFORT_LEVEL` in your environment rather than relying on text phrases, which are cosmetic in newer models.

---

## 3. Prompting Effectively

### The five-part prompt formula

Every strong prompt includes these components. Most bad prompts are missing one.

```
WHAT:   [Concrete deliverable in one sentence]
WHERE:  [Exact file paths]
HOW:    [Constraints, approach, what must not change]
VERIFY: [Tests, commands, expected output that prove it's done]
NEXT:   [Plan before edits, or small diffs]
```

**Example:**
```
Add input validation to the login form.
WHERE: src/components/LoginForm.tsx
HOW: Use Zod schema, show inline errors, no new dependencies
VERIFY: Empty email shows error, invalid format shows error, run npm test
```

### Before/after prompt comparison

From Anthropic's official guide:

| Weak | Strong |
|---|---|
| `"add tests for foo.py"` | `"write a test for foo.py covering the edge case where the user is logged out. avoid mocks."` |
| `"fix the login bug"` | `"users report login fails after session timeout. check the auth flow in src/auth/, especially token refresh. write a failing test reproducing the issue, then fix it"` |
| `"add a calendar widget"` | `"look at HotDogWidget.php as a pattern. implement a new calendar widget that lets the user select a month and paginate. build from scratch without new libraries."` |
| `"make the dashboard look better"` | `"[paste screenshot] implement this design. take a screenshot of the result and compare it to the original. list differences and fix them"` |
| `"the build is failing"` | `"the build fails with this error: [paste error]. fix it and verify the build succeeds. address the root cause, don't suppress the error"` |

### Reference files directly

```
@src/auth/session.ts    # Claude reads the file before responding
@src/api/              # Reference entire directory
```

Use tab-completion in the terminal to add file paths accurately.

### Provide rich context

- Paste images directly: drag and drop screenshots or design mocks into the prompt
- Give URLs for documentation and API references
- Pipe data: `cat error.log | claude -p "explain these errors"`
- Let Claude fetch context itself: `Use 'foo-cli-tool --help' to learn about foo, then use it to solve X`

### Challenge Claude's output

- After a mediocre fix: `"knowing everything you know now, scrap this and implement the elegant solution"`
- For verification: `"grill me on these changes and don't make a PR until I pass your test"`
- For confidence testing: `"prove to me this works"` and have Claude diff between main and your branch

### When vague prompts work

Vague prompts are useful during exploration: `"what would you improve in this file?"` can surface issues you would not have thought to ask about. Reserve precision for implementation.

---

## 4. Context Management

### Why this matters

A fresh monorepo session burns about 20K tokens loading the system prompt, tool definitions, and CLAUDE.md before you type anything. Each MCP server adds tool schemas that permanently consume context. The practical limit is about 5–8 MCP servers before you start crowding out real work.

Claude's output starts degrading at 20–40% of the window, well before any hard limit. Auto-compaction fires at roughly 83.5% and is lossy: one developer lost 3 hours of refactoring work when compaction erased all knowledge of migration decisions mid-session, retaining only 20–30% of the details.

### Context thresholds

| Usage | Status | Action |
|---|---|---|
| 0–50% | Green | Work freely |
| 50–70% | Yellow | Be selective, plan next steps |
| 70–90% | Orange | Run `/compact` now |
| 90%+ | Red | `/clear` required immediately |

Track usage with the status line: `Model: Sonnet | Ctx: 89.5k | Cost: $2.11 | Ctx(u): 56.0%`

Add to `~/.claude/settings.json`:
```json
{
  "statusLine": {
    "type": "command",
    "command": "npx -y ccstatusline@latest",
    "padding": 0
  }
}
```

### The Document and Clear pattern

The most important context management technique. When context gets heavy:

1. Dump current plan and progress to a markdown file
2. Run `/clear` to reset the session
3. Start fresh with Claude reading that file

This gives you a full 200K window with only what you choose to preserve. It is better than `/compact` because you control exactly what survives.

### The /catchup command

Create `.claude/commands/catchup.md` to rebuild context efficiently after a clear:

```markdown
Rebuild context after a /clear. Read all files modified on the
current branch compared to main. For each file, understand the
changes made. Then summarize what's been implemented so far and
what work remains.

Changed files on this branch:
$ git diff --name-only main
```

After clearing, run `/catchup` and Claude picks up where you left off without the old conversation bloat.

### One task per conversation

Starting fresh costs 20K tokens. That is nothing compared to the quality loss from a polluted session. Starting fresh after two failed corrections on the same issue almost always outperforms continuing in the same session.

### Subagents for investigation

When researching a codebase, Claude reads many files, all of which consume your main context. Use subagents for investigation:

```
Use subagents to investigate how our authentication system handles token
refresh, and whether we have any existing OAuth utilities I should reuse.
```

The subagent explores and reports back with a summary, without consuming your main context. Also useful for verification after implementation:

```
use a subagent to review this code for edge cases
```

### Context commands

| Command | Action |
|---|---|
| `/clear` | Full reset — fresh start |
| `/compact` | Summarize and free context (lossy) |
| `/compact Focus on the API changes` | Focused compaction |
| `/rewind` | Undo recent changes, restore checkpoints |
| `/btw [question]` | Side question — answer never enters conversation history |
| `Esc` | Stop Claude mid-action, context preserved |
| `Esc + Esc` | Open rewind menu |

### Lazy tool loading

One project recovered 15,000 tokens per session by using `UserPromptSubmit` hooks to inject skill definitions only when the user's prompt triggered relevant keywords, rather than pre-loading everything at startup.

---

## 5. Hooks as Deterministic Guardrails

CLAUDE.md instructions are followed roughly 70% of the time. For safety-critical rules — do not push to main, do not delete production data, always run the formatter — hooks enforce them at 100%.

### Hook types

- **`PreToolUse`** — runs before a tool executes, can block the action
- **`PostToolUse`** — runs after a tool executes, non-blocking feedback
- **`UserPromptSubmit`** — runs before processing user input
- **`Stop`** — runs when Claude finishes a turn

Exit code 2 from a PreToolUse hook blocks the action and forces Claude to try something else. Exit code 0 continues.

### Auto-formatting hook

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write \"$CLAUDE_FILE_PATHS\""
          }
        ]
      }
    ]
  }
}
```

### Safety enforcement hook

Block destructive commands and direct pushes to main:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/safety-check.sh"
          }
        ]
      }
    ]
  }
}
```

The safety-check script inspects `$CLAUDE_TOOL_INPUT` and exits 2 to block commands like `rm -rf` or `git push origin main`.

### Anti-rationalization gate

Community-tested pattern: use a PostToolUse hook that calls a secondary model (Haiku is cost-effective) to review Claude's responses for premature declarations of completion — phrases like "pre-existing issues" or "out of scope." When caught, the hook rejects the response and forces Claude to continue.

### Hook trap to avoid

Never block Edit or Write tools mid-plan. Blocking at write time breaks multi-step reasoning because Claude loses track of where it was. Let it finish writing, then validate through PostToolUse hooks or pre-commit checks.

### Permission allowlisting

Use `/permissions` to reduce interruptions for safe operations:

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Write(src/**)",
      "Bash(git *)",
      "Bash(npm run *)"
    ],
    "deny": [
      "Read(.env*)",
      "Write(production.config.*)",
      "Bash(rm *)",
      "Bash(sudo *)"
    ]
  }
}
```

Use `/sandbox` for OS-level isolation that restricts filesystem and network access. This reduces permission prompts by about 84% internally while keeping safety intact.

Use `--dangerously-skip-permissions` only in a sandbox without internet access, for contained workflows like fixing lint errors or generating boilerplate.

---

## 6. Test-Driven Development

TDD is the single strongest pattern for agentic coding. Without tests, Claude's only way to verify its work is its own judgment, which degrades as context fills. Tests create an external oracle that stays accurate regardless of session length.

### The TDD workflow (Anthropic's recommended sequence)

```
Step 1: Write tests first
"Write tests for the auth module using pytest. TDD approach, no mock implementations."

Step 2: Confirm tests fail
"Run the tests. They should all fail."

Step 3: Commit the failing tests as a checkpoint

Step 4: Implement until green
"Write the implementation. Do not modify the tests. Keep going until all tests pass."
```

The last instruction matters more than it looks. Claude will sometimes change tests to make them pass rather than fixing the implementation. Committing tests beforehand gives you a safety net: if Claude alters them, the diff shows exactly what changed.

### Mutation-resistant assertions

Write assertions that catch real behavior, not just that code runs:

```python
# Weak — passes even if the function does nothing
assert result

# Strong — catches actual behavior
assert result.status == 'completed'
assert result.timestamp is not None
assert notification_service.was_called_with(user_id=user.id)
```

An assertion against `true` passes if the code does nothing. Mutation-resistant assertions require every side effect to actually happen.

### Safe refactoring

Before refactoring, write characterization tests that lock in current behavior:

```
Refactor this module for readability without changing behavior.

First, write characterization tests that lock in current behavior.
Then refactor in small commits with explanations.
Call out any behavior changes you suspect.
```

### Visual verification loop

For frontend work with a browser tool (Playwright MCP or Claude in Chrome extension): provide Claude a design mock and let it take a screenshot after implementing, compare it to the mock, and iterate. This produces a 2–3x quality improvement over text-only verification.

---

## 7. Git Workflows and Safety

### Branch per task

Always start by creating a new Git branch for every feature or bug fix. This is the most important safety practice — if things go completely wrong, delete the branch and start over.

```
Create a new branch for this feature, then implement the OAuth flow.
```

### Commit frequently

Commit at least once per completed task, ideally once per hour during active development. Treat commits as checkpoints you can roll back to, not just a final step before PRs.

### Git worktrees for parallel development

Git worktrees let you check out multiple branches into different directories and run multiple isolated Claude instances simultaneously:

```bash
git worktree add ../feature-auth feature/auth
git worktree add ../feature-payments feature/payments

# Run Claude in each worktree independently
cd ../feature-auth && claude
cd ../feature-payments && claude
```

Engineers at incident.io run 4–5 parallel Claude sessions on separate branches. One engineer spent $8 in Claude credit and produced an implementation that saved 30 seconds on a tool used by the entire team daily.

### Writer/Reviewer pattern with parallel sessions

Use separate sessions to get unbiased review:

**Session A (Writer):** `Implement a rate limiter for our API endpoints`

**Session B (Reviewer):** `Review the rate limiter implementation in @src/middleware/rateLimiter.ts. Look for edge cases, race conditions, and consistency with our existing middleware patterns.`

**Session A (Writer):** `Here's the review feedback: [Session B output]. Address these issues.`

A reviewer session that did not write the code will not be biased toward its own work.

### Checkpoints and rewind

Claude automatically checkpoints before changes. Double-tap Escape or run `/rewind` to open the rewind menu. You can restore conversation only, restore code only, restore both, or summarize from a selected message.

Checkpoints persist across sessions. You can close your terminal and still rewind later. This is not a replacement for git — checkpoints only track changes made by Claude, not external processes.

---

## 8. Custom Commands, Skills, and Subagents

### Custom slash commands

Create reusable prompt templates in `.claude/commands/`:

```bash
mkdir -p .claude/commands
echo "Analyze this code for performance issues and suggest optimizations:" > .claude/commands/optimize.md
```

Commands with arguments:

```bash
echo 'Fix issue #$ARGUMENTS following our coding standards' > .claude/commands/fix-issue.md
# Usage: /fix-issue 123
```

Advanced command with injected shell context:

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Create a git commit with context
---

## Context
Current status: !`git status`
Current diff: !`git diff HEAD`
Current branch: !`git branch --show-current`

Create a meaningful commit message based on the changes above.
```

Save commands that you run more than once a day. Put them in `.claude/commands/` so they are checked into git and available to the team.

### Skills

Skills give Claude domain knowledge and reusable workflows. Unlike commands, skills are invoked via natural language trigger or directly with `/skill-name`.

Create `.claude/skills/api-conventions/SKILL.md`:

```markdown
---
name: api-conventions
description: REST API design conventions for our services
---

## API Conventions
- Use kebab-case for URL paths
- Use camelCase for JSON properties
- Always include pagination for list endpoints
- Version APIs in the URL path (/v1/, /v2/)
```

Skills for repeatable workflows (invoked manually, with `disable-model-invocation: true` to prevent accidental triggering):

```markdown
---
name: fix-issue
description: Fix a GitHub issue end-to-end
disable-model-invocation: true
---

Analyze and fix GitHub issue: $ARGUMENTS.

1. Use `gh issue view` to get issue details
2. Understand the problem described in the issue
3. Search the codebase for relevant files
4. Implement the necessary changes to fix the issue
5. Write and run tests to verify the fix
6. Ensure code passes linting and type checking
7. Create a descriptive commit message
8. Push and create a PR
```

Usage: `/fix-issue 1234`

**Skill authoring tips** (from the Claude Code team):
- The `description` field is a trigger, not a summary — write it as "when should I fire?"
- Build a Gotchas section in every skill — the highest-signal content, add Claude's failure points over time
- Do not state the obvious — focus on what pushes Claude out of its default behavior
- Do not railroad Claude with prescriptive steps — give goals and constraints
- Use `context: fork` to run a skill in an isolated subagent so the main context only sees the final result
- Embed `!command` in SKILL.md to inject dynamic shell output at invocation time

### Subagents

Subagents run in their own context with their own allowed tools. Use them for tasks that read many files or need specialized focus.

Create `.claude/agents/security-reviewer.md`:

```markdown
---
name: security-reviewer
description: Reviews code for security vulnerabilities
tools: Read, Grep, Glob, Bash
model: opus
---

You are a senior security engineer. Review code for:
- Injection vulnerabilities (SQL, XSS, command injection)
- Authentication and authorization flaws
- Secrets or credentials in code
- Insecure data handling

Provide specific line references and suggested fixes.
```

Invoke explicitly: `"Use a subagent to review this code for security issues."`

**Subagent tips:**
- Say `"use subagents"` to throw more compute at a problem and keep the main context clean
- Use test-time compute: one agent produces code, another (same model, fresh context) finds bugs
- Use feature-specific subagents with skills rather than generic `qa` or `backend engineer` agents
- Agent teams with tmux and git worktrees enable true parallel development on the same codebase

### Commands vs. skills vs. subagents

| Feature | Location | Use when |
|---|---|---|
| Command | `.claude/commands/<name>.md` | User-invoked prompt templates, workflow orchestration |
| Skill | `.claude/skills/<name>/SKILL.md` | Auto-discoverable domain knowledge, progressive disclosure |
| Subagent | `.claude/agents/<name>.md` | Isolated context, specialized tools, parallel work |

For small, well-defined repeating tasks: vanilla Claude Code with a command is better than a complex workflow. Only add subagents when context isolation genuinely matters.

---

## 9. Session Workflow Reference

### Typical session flow

```
1. Start session      → claude
2. Check context      → /status
3. Plan Mode          → Shift+Tab × 2 (for complex or risky tasks)
4. Describe task      → Specific prompt with WHAT, WHERE, HOW, VERIFY
5. Review changes     → Always read every diff before accepting
6. Accept/Reject      → y/n
7. Verify             → Run tests
8. Commit             → When task is complete
9. Next task          → /clear between unrelated tasks
```

### Course-correcting

- `Esc` — stop Claude mid-action (context preserved, you can redirect)
- `Esc + Esc` or `/rewind` — restore previous conversation and code state
- `"Undo that"` — have Claude revert its changes
- `/clear` — reset context between unrelated tasks

If you have corrected Claude more than twice on the same issue, run `/clear` and start fresh with a more specific prompt that incorporates what you learned.

### Resume sessions

```bash
claude --continue    # Resume the most recent conversation
claude --resume      # Select from recent conversations
```

Use `/rename` to give sessions descriptive names like `"oauth-migration"` or `"debugging-memory-leak"` so you can find them later. Treat sessions like branches: different workstreams get separate, persistent contexts.

### The /wizard 8-phase methodology

Community-tested pattern for complex features with high correctness requirements:

1. **Plan** — read CLAUDE.md, find the issue, build a structured todo list before any code is written
2. **Explore** — grep for every model, method, and constant the plan references and verify they exist
3. **Write tests first** — failing tests, mutation-resistant assertions, run them to confirm they fail
4. **Implement minimum** — minimum code to make tests pass, no scope creep
5. **Verify no regressions** — run the full related test suite
6. **Document** — inline comments and changelog while context is fresh
7. **Adversarial review** — review as an attacker: race conditions, null inputs, wrong assumptions
8. **Quality gate cycle** — open PR, monitor automated review, fix valid findings, repeat until clean

The adversarial review checklist:
- What happens if this runs twice concurrently?
- What if the input is null, empty, or negative?
- What assumptions am I making that could be wrong?
- Would I be embarrassed if this broke in production?

Install the wizard skill: `curl -sL https://raw.githubusercontent.com/vlad-ko/claude-wizard/main/install.sh | bash`

---

## 10. Model Selection and Cost

### Model selection guide

| Task | Model | Effort |
|---|---|---|
| Rename, boilerplate, typos, simple validation | Haiku | low |
| Feature development, debugging, refactoring, test writing | Sonnet | medium–high |
| Architecture decisions, security audits, complex bugs | Opus | high |

Use **OpusPlan** mode (`/model opusplan`) to get Opus-quality reasoning for planning while auto-switching to Sonnet for code generation. This captures the reasoning quality where it matters most at 5x lower cost for implementation tokens.

### Dynamic model switching

Start with Sonnet, switch to Opus when you hit complexity, switch back after:

```bash
# Session start (default Sonnet)
claude

# Complex feature encountered
/model opus    # Switch to deep reasoning

# Feature complete, back to routine work
/model sonnet  # Speed + cost optimization
```

Switch on task boundaries, not mid-task.

### Cost comparison (API pricing)

| Model | Input | Output | Use case |
|---|---|---|---|
| Haiku | $0.25/MTok | $1.25/MTok | Simple fixes (5–10% of tasks) |
| Sonnet | $3/MTok | $15/MTok | Most development (70–80% of tasks) |
| Opus | $15/MTok | $75/MTok | Complex reasoning (10–20% of tasks) |

### Subscription vs. API pricing

Anthropic reports average Claude Code cost at $6/developer/day on API pricing, with 90% of developers under $12/day. The Max subscription changes this significantly: one developer tracked 8 months of usage and found API-equivalent cost exceeded $15,000 while his actual Max subscription cost was about $800 — a 93% savings. The breakeven point for the Max plan sits at roughly $100–200/month in API-equivalent usage.

| Plan | Monthly Cost | Best for |
|---|---|---|
| API (Sonnet) | ~$100–200 | Light usage, under 30 min/day |
| API (Opus) | ~$300–800 | Complex multi-file work |
| Max ($100/mo) | $100 flat | Daily users, breakeven at ~$100 API equivalent |
| Max ($200/mo) | $200 flat | Power users, 5+ hours/day |

Over 90% of Max plan tokens are cache reads, which is why metered API pricing hits harder than flat subscription.

### Token waste reduction

Fixing these three issues typically cuts token usage in half:
1. Not clearing context between tasks
2. Redundant file reads from poor CLAUDE.md structure (inlining large docs)
3. Vague prompts that send Claude into trial-and-error loops

---

## 11. Automation and CI/CD

### Non-interactive (headless) mode

```bash
# One-off query
claude -p "Explain what this project does"

# Structured output for scripts
claude -p "List all API endpoints" --output-format json

# Streaming for real-time processing
claude -p "Analyze this log file" --output-format stream-json

# With specific tools only
claude -p "fix typos" --allowedTools "Edit,Bash(git commit *)"

# With budget cap
claude -p "analyze this" --max-budget-usd 5.00
```

### Fan-out pattern for large migrations

```bash
# Step 1: Generate task list
claude -p "list all Python files that need migrating to async" > files.txt

# Step 2: Process in parallel
for file in $(cat files.txt); do
  claude -p "Migrate $file from sync to async. Return OK or FAIL." \
    --allowedTools "Edit,Bash(git commit *)" &
done
wait

# Step 3: Test on 2-3 files first, then run at scale
```

The `--allowedTools` flag restricts scope when running unattended.

### Hooks in CI/CD

Run linting, type checking, and tests automatically after every file edit without manual intervention. Set up via `.claude/settings.json` PostToolUse hooks.

### Key CLI flags

| Flag | Usage |
|---|---|
| `-p "prompt"` | Non-interactive mode |
| `-c` / `--continue` | Continue last session |
| `-r` / `--resume <id>` | Resume specific session |
| `--model claude-sonnet-4-6` | Change model |
| `--add-dir ../lib` | Allow access outside CWD |
| `--allowedTools "Edit,Read"` | Whitelist tools |
| `--max-turns 3` | Limit conversation turns |
| `--output-format json` | Structured output |
| `--output-format stream-json` | Streaming output |
| `--verbose` | Debug logging (turn off in production) |
| `--dangerously-skip-permissions` | Auto-accept (sandbox only) |
| `-w` / `--worktree` | Run in isolated git worktree |

---

## 12. Production-Quality Code Guardrails

From a community-tested CLAUDE.md template focused on operability and security:

### Three-tier responsibility model

Define what Claude does vs. what humans do:

- **Tier 1 (Claude does it)**: in-code practices — error handling, structured logging, input validation
- **Tier 2 (Claude scaffolds, you operationalize)**: Dockerfiles, CI configs, IaC templates — Claude proposes, you review and deploy
- **Tier 3 (you do it)**: secrets infrastructure, compliance decisions, incident response, SLO definitions — Claude should flag these gaps rather than silently invent workarounds

When Claude hits a Tier 3 dependency, it should produce a `REQUIRES:` or `FLAG:` annotation instead of guessing.

### Security rules for CLAUDE.md

```markdown
## Security
- Never hardcode credentials, API keys, or connection strings
- Use environment variables or secrets manager for all secrets
- Log secrets to REQUIRE when secrets infrastructure is not configured
- Validate all external input before use
- Use parameterized queries, never string concatenation for SQL

## DO NOT
- Commit .env files or any file containing credentials
- Write tests that only cover the happy path
- Swallow exceptions silently
- Hardcode connection strings, table names, or category strings

## REQUIRE (flag to developer if missing)
- Secrets manager is configured before adding any credential handling
- Auth provider is configured before implementing authentication
- Log aggregation is configured before adding structured logging
```

### AWS MCP safety pattern

When using AWS MCP: connect with read-only credentials and have Claude propose all changes as CloudFormation templates with a cost summary. Do not give Claude write access to cloud infrastructure. Cost traps to flag explicitly: NAT Gateways, unattached EIPs, CloudWatch Logs with no retention policy.

### Pre-production checklist prompt

Before deploying, run:

```
Review all REQUIRE and FLAG items in your recent work. For each one, produce
a table with columns: Item | Status (addressed/not-addressed/not-applicable) | Notes
```

---

## 13. Anti-Patterns to Avoid

| Anti-pattern | What happens | Fix |
|---|---|---|
| The kitchen sink session | One task leads to another unrelated task; context fills with irrelevant history | `/clear` between unrelated tasks |
| Correcting over and over | Failed approaches accumulate, polluting context | After two failed corrections, `/clear` and write a better initial prompt |
| Over-specified CLAUDE.md | Long files cause Claude to lose important rules in noise | Ruthlessly prune; if Claude already does something correctly without the instruction, delete it or convert it to a hook |
| Trust-then-verify gap | Plausible-looking implementation misses edge cases | Always provide verification (tests, scripts, screenshots); if you cannot verify it, do not ship it |
| Infinite exploration | "investigate X" without scope reads hundreds of files, fills context | Scope investigations narrowly or use subagents |
| Vague definition of done | Code looks right but is not proven | Add test command, expected output, or minimal reproduction to every prompt |
| Unreviewable diffs | Large changes are hard to review safely | Ask for small diffs and a plan; require commits at task boundaries |
| Accepting without reading | Bugs ship unreviewed | Read every diff before accepting |
| Using --dangerously-skip-permissions outside a sandbox | Risk of data loss, system corruption, or prompt injection | Only use in isolated environments without internet access |
| Giving Claude write MCP access to production infrastructure | Accidental resource creation, surprise costs | Use read-only MCP credentials; Claude proposes changes as IaC templates |

---

## 14. Quick Reference: Commands and Shortcuts

### Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Shift+Tab × 2` | Enter Plan Mode |
| `Shift+Tab × 1` | Cycle through permission modes |
| `Esc` | Interrupt Claude (context preserved) |
| `Esc × 2` | Open rewind menu |
| `Ctrl+C` | Hard interrupt |
| `Ctrl+R` | Search command history |
| `Ctrl+G` | Open current plan in editor |
| `Alt+T` | Toggle thinking on/off |
| `Shift+Enter` | New line in prompt |
| `Space (hold)` | Voice input (requires `/voice` enabled) |

### Essential slash commands

| Command | Action |
|---|---|
| `/help` | Show all commands including custom |
| `/plan` | Enter Plan Mode |
| `/execute` | Exit Plan Mode |
| `/clear` | Reset conversation |
| `/compact` | Summarize and free context |
| `/compact Focus on API changes` | Focused compaction |
| `/status` | Session state and context usage |
| `/context` | Detailed token breakdown |
| `/model` | Switch model |
| `/model opusplan` | Opus for planning, Sonnet for execution |
| `/config` | Configure settings interactively |
| `/hooks` | Browse configured hooks |
| `/permissions` | Configure tool allowlist |
| `/sandbox` | Enable OS-level isolation |
| `/rewind` | Undo and restore checkpoints |
| `/rename [name]` | Name the current session |
| `/btw [question]` | Side question, no history pollution |
| `/loop [interval] [prompt]` | Run a prompt on a schedule |
| `/simplify` | Detect and fix over-engineering |
| `/batch` | Large-scale refactors via parallel agents |
| `/agents` | Manage subagents |
| `/mcp` | MCP server status |
| `/doctor` | Diagnose installation issues |
| `/init` | Generate CLAUDE.md from codebase |
| `/clear` | Reset context |

### .claude/ folder structure

```
.claude/
├── CLAUDE.md              # Local memory (gitignore or commit — your choice)
├── settings.json          # Hooks and team settings (commit to git)
├── settings.local.json    # Personal permission overrides (do not commit)
├── agents/                # Custom subagent definitions
├── commands/              # Slash command templates
├── hooks/                 # Event scripts
├── rules/                 # Auto-loaded rule files
└── skills/                # Knowledge modules with SKILL.md files
```

### Debug commands

```bash
claude --version          # Check version
claude update             # Update to latest
claude doctor             # Run diagnostics
claude --debug            # Verbose output
claude --mcp-debug        # Debug MCP connections
```

### Quick decision tree

```
Simple, clear task          → Ask Claude directly
Complex or risky task       → Plan Mode first (Shift+Tab × 2)
Repeating task (daily)      → Create a command or skill
Context over 70%            → /compact
Stuck in wrong direction    → /clear and start with better prompt
Need isolated investigation → "Use subagents to investigate X"
Need parallel work          → Git worktrees + multiple sessions
Need deterministic behavior → Hooks, not CLAUDE.md instructions
```

---

## Sources

- **Anthropic official guide**: `code.claude.com/docs` — Best Practices for Claude Code
- **DataCamp**: "Claude Code Best Practices: Planning, Context Transfer, TDD" (March 2026)
- **PhotoStructure**: "Claude picks the first idea that works. Make it pick the best one." (March 2026)
- **DEV Community**: "I Made Claude Code Think Before It Codes. Here's the Prompt." (March 2026)
- **shanraisshan/claude-code-best-practice** (GitHub, 20.4k stars, March 2026)
- **FlorianBruniaux/claude-code-ultimate-guide** cheatsheet (GitHub, 2.1k stars, March 2026)
- **Dinanjana Gunaratne** (Medium): "Mastering the Vibe: Claude Code Best Practices That Actually Work"
- **eesel AI**: "7 Claude Code best practices for 2026 (from real projects)"
- **QuantumByte**: "Claude Code Prompts: Best Templates and Developer Practices"
- **Shipyard**: "Claude Code CLI Cheatsheet: config, commands, prompts, + best practices"
- **AWS**: "Claude Code deployment patterns and best practices with Amazon Bedrock" (November 2025)
- **Reddit r/ClaudeCode**: Opinionated CLAUDE.md template focused on security and operability
