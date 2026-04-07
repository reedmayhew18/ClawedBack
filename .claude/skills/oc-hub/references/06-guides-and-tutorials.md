# Claude Code: Guides and Tutorials

A learning progression from first session to production-grade agentic systems. Content synthesized from official guides, practitioner write-ups, video tutorials, and real-world usage reports. See also `05-workflows-and-automation.md` for Loop, Hooks, CI/CD, and the Ralph Loop.

> Note: File `73-PyTorch-Training-Loop-A-Production-Ready-Template-for-AI-Engineers.md` exists in the source directory but covers PyTorch training infrastructure, not Claude Code specifics. It is not summarized here.

---

## Table of Contents

1. [Getting Started: What Claude Code Actually Is](#getting-started)
2. [Core Concepts for Non-Technical Users](#core-concepts)
3. [The Two-Habit Framework (Dean Blank)](#two-habit-framework)
4. [The Seven Levels of Mastery](#seven-levels)
5. [Advanced Features Reference](#advanced-features)
6. [Python Customization Architecture (Syed Asif)](#python-customization)
7. [Pedro Sant'Anna's Academic Workflow](#pedros-workflow)
8. [Deep Research Report: Strategic Orchestration](#deep-research-report)
9. [Claude Models and Features (2026)](#claude-2026)
10. [MLflow Integration](#mlflow-integration)
11. [Business Applications](#business-applications)

---

## 1. Getting Started: What Claude Code Actually Is {#getting-started}

Claude Code is an agentic coding assistant — not a chatbot. It reads, writes, and edits your actual files, runs terminal commands, manages Git workflows, and operates directly on your codebase across an entire session with persistent context.

### Installation

```bash
npm install -g @anthropic-ai/claude-code
cd your-project
claude
```

Requires a Claude Pro, Max, Team, or Enterprise account. Run `claude` in your project directory to start a session with full access to everything in that directory.

### The Three Modes

Cycle between modes with `Shift+Tab`:

| Mode | Behavior |
|---|---|
| Normal | Asks approval before risky actions (file writes, shell commands) |
| Auto-Accept | Applies file edits without asking; still prompts for shell commands |
| Plan | Read-only. Claude can explore and propose but cannot change anything |

Start complex tasks in Plan mode. Switch to Normal or Auto-Accept once the plan looks right.

### Essential Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Shift+Tab` | Cycle between Normal / Auto-Accept / Plan |
| `Ctrl+C` | Stop current action |
| `Esc+Esc` | Undo last change |
| `?` | Show all shortcuts |

### Essential Slash Commands

| Command | Purpose |
|---|---|
| `/init` | Create CLAUDE.md in project root |
| `/compact` | Summarize context to free window space |
| `/clear` | Start fresh (new context window) |
| `/memory` | View and edit user-level memory |
| `/doctors` | Diagnose environment issues |
| `/review` | Code review current changes |
| `/simplify` | Review code for reuse, quality, efficiency |

---

## 2. Core Concepts for Non-Technical Users {#core-concepts}

These 27 concepts cover what Claude Code is, what it can do, and how to think about it — no technical background required.

### The Fundamentals

**CLAUDE.md** is a configuration file at the root of your project. Claude reads it at the start of every session. Put your tech stack, naming conventions, test commands, and rules in here. Claude treats it as standing instructions — it always knows what's in there.

**Context window** is the working memory for a session. Every file read, command output, and message consumes space. When context gets full, use `/compact` to summarize it or `/clear` to start fresh. Claude will warn you when context is getting heavy.

**Plan Mode** is a read-only mode where Claude can explore your project and suggest a plan but cannot make changes. Use it before any complex task. Ten seconds of planning prevents ten minutes of undoing.

**Hooks** are scripts that run automatically when certain events happen — before Claude edits a file, after a tool runs, when a session starts. They enforce rules deterministically, independent of what the model decides. See `05-workflows-and-automation.md` for the full hooks reference.

**MCP (Model Context Protocol)** is the standard for connecting Claude to external tools and data sources — databases, APIs, Slack, GitHub, internal systems. Think of it as USB-C for AI. Any system wrapped as an MCP server becomes available as a tool Claude can call.

**Sub-agents** are separate Claude instances spawned for isolated tasks. They run in their own context windows so heavy workloads stay out of your main session. Only a summary returns. Useful when a task touches more than five files.

**Skills** are packaged workflows stored as markdown files with YAML frontmatter. They tell Claude how to perform a specific multi-step process. Install them with `npx skills add <package>` or build your own in `~/.claude/skills/`.

**Headless mode** runs Claude non-interactively for scripts and CI pipelines:

```bash
claude -p "review these changes for bugs" < diff.txt
git diff --cached | claude -p "check for security issues"
```

### What Claude Code Can and Cannot Do

Can do: read/write files, run bash commands, call APIs via MCP, manage Git, run tests, write and execute code, spawn sub-agents, chain multi-step workflows.

Cannot do (without explicit setup): access the internet directly (use web-fetch MCP tools), persist state across sessions without CLAUDE.md or external storage, take actions you have not approved in Normal mode.

---

## 3. The Two-Habit Framework {#two-habit-framework}

*From Dean Blank, Senior Machine Learning Engineer, Fintech.*

The people getting the most out of Claude Code are not writing magic prompts. They are investing in two categories of habit.

> "Boris Cherny, the creator of Claude Code, has said his own setup is 'surprisingly vanilla.' He doesn't heavily customize, because the tool is already powerful on its own. The edge comes from the habits, not from complex configs."

### Category 1: Compounding Habits (Set Up Once)

These pay dividends every session from the moment you establish them.

**Maintain CLAUDE.md.** Run `/init` to create it. Fill it with your tech stack, build and test commands, and any conventions you want enforced. Keep it under 200 lines. If it grows too long, move rules into `.claude/rules/` — Claude loads those the same way and you can scope them to specific file types.

The key habit: every time Claude does something wrong, add a note to CLAUDE.md so it cannot happen again. The Claude Code team at Anthropic calls this "compounding engineering." Each correction becomes permanent context — Claude never makes that class of error again. On a team, every rule one person adds benefits everyone else automatically.

**Give Claude feedback loops.** Tell Claude to run tests, linters, or build commands after every change. Without a feedback loop, Claude makes changes, assumes they work, and moves on. With one, it catches its own mistakes. Boris Cherny has said this alone can 2–3x output quality. One line in CLAUDE.md is sufficient:

```
Always run pytest after changing Python files.
```

### Category 2: Session Habits (Apply Each Time)

**Start complex tasks in Plan mode.** If a task touches multiple files or requires research, switch to Plan mode first. For single-line changes, skip it. Push back if the plan looks off, then switch to Normal or Auto-Accept and say "implement."

**Be specific and reference files directly.**

Instead of:
> "Fix the authentication bug."

Say:
> "Fix the off-by-one error in @utils.py around line 42 that skips the last item."

A detailed prompt up front saves multiple corrective round trips.

**Protect your context window.** Every file read, command output, and exchange eats into context. Use `/compact` to summarize for large tasks, or `/clear` between unrelated tasks.

**Keep tasks small.** "Build me a full e-commerce site with auth, payments, and checkout" is ten tasks in one. Break it up: "Create a plan for a full e-commerce site with auth, payments, and checkout, then break it into waves." Tackle each wave one at a time, clearing context between them.

### Common Pitfalls

**Claude ignores your project conventions.** It writes code that works but uses snake_case when your codebase uses camelCase. This is almost always a missing CLAUDE.md rule. Add `Always use camelCase for variables and PascalCase for classes` — Claude follows from that point on.

**A complex task spirals.** Claude starts editing files you did not expect. Stop it with `Ctrl+C`, rewind with `Esc+Esc` if needed, switch to Plan mode, and break the task into smaller pieces.

---

## 4. The Seven Levels of Mastery {#seven-levels}

Progression from basic usage to fully autonomous pipelines. Each level builds on the previous.

### Level 1: Basic Prompting

Single-turn requests for code generation, explanation, and debugging. Claude responds to natural language but has no persistent context.

**Unlocks:** Writing code faster. Explaining unfamiliar codebases.

### Level 2: Context Loading

Loading relevant files with `@filename` references. Claude reads the actual code before responding. Answers become project-specific instead of generic.

**Unlocks:** Accurate refactoring. Bug fixes that understand the surrounding code.

### Level 3: Plan Mode Discipline

Switching to Plan mode for complex tasks. Claude produces a structured plan with file-by-file breakdown before touching anything. You review and approve before execution begins.

**Unlocks:** Multi-file changes that do not spiral. Confidence in scope before committing.

### Level 4: CLAUDE.md Configuration

Writing and maintaining CLAUDE.md. Claude enters every session knowing your stack, conventions, and hard rules. Correction becomes permanent rather than repeated.

**Unlocks:** Consistent output quality. Team-wide standards enforced automatically.

### Level 5: Feedback Loops and Hooks

Wiring Claude to tests, linters, and build commands. Claude runs verification after every change and self-corrects. Hooks enforce deterministic rules (banned patterns, format checks) outside of model judgment.

**Unlocks:** Claude catching its own mistakes. Guaranteed style and security rules.

### Level 6: Sub-agents and Skills

Using sub-agents to isolate heavy workloads. Using skills to package complex workflows. Claude spawns specialized workers for parallelizable tasks and invokes them by name.

**Unlocks:** Large-scale parallel research. Consistent multi-step workflows. Context stays clean in the main session.

### Level 7: Autonomous Pipelines

Fully automated workflows: headless sessions in CI/CD, scheduled tasks via `/loop`, event-driven reactions via Channels, multi-agent orchestration with a Conductor pattern.

**Unlocks:** Code that ships automatically after passing quality gates. Monitoring that reacts to production events without human triage.

---

## 5. Advanced Features Reference {#advanced-features}

### Headless / Pipe Mode

```bash
claude -p "prompt" [--output-format json|text|stream-json]
```

Use in scripts, git hooks, and CI pipelines. The `--output-format json` flag returns structured results for programmatic parsing.

```bash
# Pre-commit hook example
git diff --cached | claude -p "review staged changes for security issues" --output-format json
```

### Worktrees for Parallel Sessions

```bash
claude --worktree feature-auth
```

Creates an isolated git worktree. Run multiple Claude sessions on different branches simultaneously with no conflicts.

### Sub-agents

Claude Code ships with built-in sub-agents (Explore, Plan, general-purpose) that spawn in their own context windows. Claude uses them automatically when tasks call for isolation. You can also direct them explicitly:

> "Spin up three sub-agents to research the authentication module, the database layer, and the API routes in parallel, then summarize what you find."

Rule of thumb: if a task touches more than five files, consider isolating it in a sub-agent.

### Custom Sub-agents and Skills

Ask Claude to generate them:

> "Create a sub-agent that reviews code for security issues."
> "Create a skill that deploys to staging."

Or build manually. Sub-agents are defined in `~/.claude/agents/` as markdown files with YAML frontmatter specifying the model, allowed tools, and disallowed tools.

### Git Integration

```bash
claude "review this PR for potential issues"
claude "create a commit message for these changes"
claude "resolve the merge conflict in src/auth.py"
```

Claude understands Git history, diffs, and branch state natively.

### IDE Integration

Claude Code integrates with VS Code and JetBrains IDEs. The in-IDE panel gives it direct access to your open files and the integrated terminal.

### Security Model

- Never commit API keys — use environment variables
- Review generated code before deployment
- Use `--allowedTools` / `--disallowedTools` flags to restrict what Claude can call
- Build custom MCP servers for sensitive systems rather than granting direct database access
- Hooks can enforce security rules deterministically (see `05-workflows-and-automation.md`)
- In regulated environments: log every MCP interaction, enforce data access rules at the MCP layer

---

## 6. Python Customization Architecture {#python-customization}

*From Syed Asif's practical guide, February 2026.*

The problem this solves: every new conversation starts from zero context. You repeat the same instructions — add type hints, handle edge cases, use logging not print — until you get working code. The four-tier architecture makes your standards permanent.

> "Time investment: 30 minutes setup + 5 min per project. Expected ROI: 5–10 minutes saved per development task (80% time reduction). Break-even: After 3–6 development tasks."

### The Four-Tier System

```
~/.claude/
├── CLAUDE.md                    # Core principles (auto-loaded)
├── rules/                       # Tier 1: ALWAYS-ON
│   ├── security.md              # Security requirements
│   ├── testing.md               # Testing requirements
│   └── tools.md                 # Standard linting/test commands
├── guidelines/                  # Tier 2: ON-DEMAND
│   ├── python.md                # Python patterns, type hints, async
│   ├── api-design.md            # RESTful principles, versioning
│   ├── database.md              # ORM usage, query optimization
│   └── documentation.md        # README format, docstrings
├── skills/                      # Tier 3: WORKFLOWS
│   ├── code-refactoring/
│   │   └── SKILL.md
│   ├── fresh-review/
│   │   └── SKILL.md
│   └── web-research/
│       └── SKILL.md
└── agents/                      # Tier 4: SPECIALIZED WORKERS
    └── code-reviewer.md
```

**Key insight:** Lower tiers provide broader context, higher tiers provide specific constraints. Progressive disclosure saves tokens while ensuring comprehensive guidance.

### Tier 1: Rules (Always-On)

Rules are automatically loaded into every conversation. Standard markdown files, no YAML frontmatter required. Use them for:

- Security requirements: input validation, secret management
- Testing requirements: coverage thresholds, verification pyramid
- Tool commands: standard linting, testing, formatting commands

Without rules, Claude generates working code with no security checks. With rules, every response automatically applies your standards.

### Tier 2: Guidelines (On-Demand)

Guidelines are reference materials explicitly loaded when needed. They are NOT auto-loaded — this saves context tokens.

```
# Before working on Python code
Read ~/.claude/guidelines/python.md

# Before designing an API
Read ~/.claude/guidelines/api-design.md
```

Include these instructions in CLAUDE.md so Claude knows when to load which guideline.

### Tier 3: Skills (On-Demand Workflows)

Skills are markdown files with YAML frontmatter. They contain step-by-step workflows, design patterns, code templates, and checklists.

```yaml
---
name: code-refactoring
description: Code modernization workflow for legacy Python
---
```

Skills load on-demand when Claude detects a relevant task. When you say "help me refactor this legacy code," Claude detects the keyword, loads the skill, and applies the modernization checklist: convert to f-strings, add type hints, use pathlib, migrate to dataclasses.

### Tier 4: Sub-agents (Specialized Workers)

Sub-agents are constrained workers for specific tasks. They can be restricted to read-only tools (safe for code review), specific tool subsets, or different models (Haiku for speed, Opus for complex analysis).

```yaml
---
name: code-reviewer
description: Semantic code review using specific skills
color: "#FFFF00"
skills:
  - code-refactoring
---
```

### The CLAUDE.md Template

The full CLAUDE.md from this guide defines a "Senior + Autonomous Software Engineer" with explicit decision boundaries:

**Independence Tier (proceed and notify):**
- Implementation strategy choices
- Internal refactoring for legibility
- Minor/patch dependency updates
- Test suite design

**Collaboration Tier (propose and wait):**
- Architecture shifts (sync to async)
- External interfaces (public API signatures, CLI arguments)
- New dependencies
- Constraint negotiation

**Strict Prohibition (never touch):**
- Secrets and auth logic
- Unrelated infrastructure (CI/CD, Docker, Terraform unless requested)
- Global formatting (never run auto-format-all on the repository)

**Engineering Lifecycle:**
1. Discovery: call-site search, pattern search, history search
2. Strategic Planning: negative planning (state what will NOT change), rollback path, subagent parallelism
3. Surgical Execution: atomic commits, no debug logs, idiomatic alignment

**Stop and Ask Triggers:**
- Security vulnerability found in unrelated code
- "Surgical scope" requires changing more than five files
- Contradictory requirements discovered
- Temptation to bypass existing architecture because "it's cleaner"

---

## 7. Pedro Sant'Anna's Academic Workflow {#pedros-workflow}

*From Pedro's public Claude Code setup documentation. Pedro is an econometrician who uses Claude Code for academic research and statistical software development.*

### The Problem It Solves

Academic research involves diverse, specialized tasks: literature review, statistical analysis, paper writing, code review. No single agent can excel at all of them. Pedro's solution is a team of ten specialized agents with an orchestrator to coordinate them.

### The Ten-Agent System

| Agent | Role |
|---|---|
| Orchestrator | Coordinates the other agents, routes tasks, enforces quality gates |
| Researcher | Literature search, paper synthesis, citation management |
| Statistician | Econometric analysis, model selection, interpretation |
| Coder | R/Python/Stata implementation, package development |
| Writer | Academic prose, paper structure, abstracts |
| Reviewer | Adversarial review of drafts and code |
| Data Manager | Dataset cleaning, documentation, reproducibility |
| Methods Checker | Validates statistical methodology against field standards |
| Replicator | Attempts to reproduce results from code and data |
| Editor | Final pass for clarity, consistency, citations |

### Quality Gates

Three scoring thresholds control when work progresses:

- **80 score:** Draft acceptable for internal review
- **90 score:** Ready for co-author review
- **95 score:** Ready for journal submission

The Orchestrator enforces these gates. No task advances until it clears the threshold for its stage.

### The Orchestrator Pattern

The Orchestrator does not do the work — it coordinates:

1. Receives the task from the user
2. Breaks it into sub-tasks appropriate for each specialist agent
3. Routes sub-tasks to the right agents
4. Collects results and applies quality gate scoring
5. Returns failed work to the originating agent with specific improvement instructions
6. Escalates to the user only when the gate cannot be cleared after iteration

This pattern separates concerns cleanly: each agent is optimized for its domain, and the orchestrator is optimized for coordination and quality enforcement.

### Context Management in Long Research Sessions

Pedro uses HANDOFF.md files to preserve state across session boundaries:

```markdown
# Handoff: Paper Draft v3
Status: Introduction complete, methods section 60%
Next task: Complete econometric identification section
Key decisions made: [list]
Blocking issues: [list]
Files modified: [list]
```

The `Document & Clear` pattern: before clearing context, produce a handoff document. The next session loads the handoff instead of reconstructing state from scratch.

---

## 8. Deep Research Report: Strategic Orchestration {#deep-research-report}

*Synthesized from the full deep research report on advanced Claude Code skills for autonomous software development.*

### The Three-Tier Knowledge Hierarchy

All customization content falls into one of three tiers based on how it should be loaded:

```
Tier 1: Rules     → Always loaded, always active
Tier 2: Guidelines → Loaded on demand by topic
Tier 3: Skills    → Loaded when a specific workflow is triggered
```

This matches the Python architecture above but applies universally. The rationale: rules are non-negotiable and must be present in every context. Guidelines are reference material — loading all of them in every session wastes tokens. Skills are procedures — they only matter when you are performing that specific task.

### The Conductor Pattern

For multi-agent systems, the Conductor pattern separates strategic direction from execution:

```
User
  └── Conductor (plans, coordinates, reviews)
        ├── Agent A (specialized execution)
        ├── Agent B (specialized execution)
        └── Agent C (specialized execution)
```

The Conductor:
- Receives the high-level goal
- Decomposes it into tasks
- Assigns tasks to appropriate agents
- Reviews results against acceptance criteria
- Routes failed tasks back for revision
- Synthesizes final output for the user

The Conductor does not execute code. It manages the workflow. This separation is what allows the system to scale — adding a new capability means adding a new agent, not modifying the coordination logic.

### Adversarial Review

One of the most powerful patterns in the report: spawn a separate agent whose sole job is to find flaws in another agent's output.

```
Writer Agent  →  produces draft
                    ↓
Reviewer Agent →  adversarial critique
                    ↓
Writer Agent  →  revision
                    ↓
(repeat until quality gate passes)
```

The Reviewer is explicitly instructed to look for problems, not to validate. This is structurally different from asking the Writer to review its own work — the same agent that produced the output has motivated reasoning to defend it.

### Context Management Patterns

**The `/compact` discipline:** Use `/compact` when context is getting heavy but you want to maintain session continuity. This summarizes the conversation history without losing the thread.

**The `Document & Clear` pattern:** For tasks spanning multiple work sessions, produce a structured handoff document before clearing context. The next session reads the handoff and resumes from a known state rather than trying to reconstruct from memory.

**Post-compaction hooks:** A `PreCompact` hook can automatically write a HANDOFF.md before compaction runs. This makes context preservation automatic rather than manual.

**Sub-agent isolation:** Delegate research-heavy tasks to sub-agents. The sub-agent accumulates a large context (reading many files, running many searches), but only a summary returns to the main session. Your main context stays clean.

### Security Governance in Agentic Systems

As agents gain more autonomy, security governance becomes critical:

**Principle of least privilege at the MCP layer:** Each MCP server should expose only the operations the agent actually needs. A code review agent should have read-only access. A deployment agent should not have database write access.

**Audit logging:** Every tool call should be logged with the agent identity, tool name, inputs, outputs, and timestamp. This is essential for debugging and compliance.

**Human approval checkpoints:** For irreversible actions (deploys, database writes, external API calls), build explicit approval steps into the workflow rather than relying on the agent to decide when approval is needed.

**Sandbox testing:** Before deploying agent workflows to production systems, test them against staging environments with production-equivalent data volumes but without real consequences.

### The GSD (Get Shit Done) Framework

A phase-based planning approach to prevent context rot in large projects:

```
Phase 1: Planning
  → Define acceptance criteria before any code is written
  → Break work into small, verifiable tasks
  → Establish test commands that will prove each task complete

Phase 2: Execution
  → Execute one task at a time
  → Verify each task against acceptance criteria before proceeding
  → Commit after each verified task (clean rollback points)

Phase 3: Review
  → Adversarial review of the completed phase
  → Quality gate: does the work meet the original acceptance criteria?
  → Document what was learned for the CLAUDE.md
```

The critical rule: never move to Phase 2 with vague acceptance criteria. "Make it work" is not acceptance criteria. "All existing tests pass and the new endpoint returns 200 for valid input and 422 for malformed input" is.

---

## 9. Claude Models and Features (2026) {#claude-2026}

*From the BuildFastWithAI 2026 overview.*

### Current Model Lineup

| Model | Context | Output | Best For |
|---|---|---|---|
| Claude Opus 4.6 | 1M tokens | 128k tokens | Complex reasoning, multi-agent coordination, long-document analysis |
| Claude Sonnet 4.6 | 200k tokens | 64k tokens | Daily development work, balanced speed and quality |
| Claude Haiku 4.5 | 200k tokens | 32k tokens | Fast responses, sub-agent workers, high-volume batch tasks |

### Adaptive Thinking

The new API parameter for extended reasoning:

```python
response = client.messages.create(
    model="claude-opus-4-6",
    thinking={
        "type": "adaptive"   # replaces deprecated budget_tokens
    },
    messages=[...]
)
```

`adaptive` allows the model to decide how much reasoning the task requires. For complex problems it allocates more internal compute; for simple tasks it responds quickly.

### Desktop App

Claude Desktop (previously web-only) now runs as a native app with:
- Local file system access without terminal
- Artifact canvas for interactive visualizations
- Direct connection to local MCP servers without configuration
- Persistent project sessions across app restarts

### Extended Output (Sonnet / Opus)

The 128k output token limit on Opus 4.6 enables:
- Generating entire files in a single response
- Producing full test suites without truncation
- Writing complete documentation sets
- Generating multi-file scaffolds in one pass

### Batch API

The Batch API processes up to 10,000 requests asynchronously at reduced cost. Use it for:
- Evaluating large test suites against multiple prompts
- Bulk code migration across a large codebase
- Running the same analysis across many documents
- Generating datasets for evaluation

---

## 10. MLflow Integration {#mlflow-integration}

*From the MLflow blog, February 2026.*

MLflow integrates with Claude Code to add observability, evaluation, and workflow automation to agentic development.

### Tip 1: Trace Every Session

```bash
mlflow autolog claude
```

Run this once in your project (or set it up at the user level). MLflow captures every session: input text, context changes, tool usage, token counts, latency. Every interaction becomes a structured trace you can search, filter, and analyze.

Captured metadata per session:
- Total token usage (input + output + cache)
- Tool call sequence and timing
- Latency per step
- Error events and permission blocks

### Tip 2: Evaluate Traces

Once traces are recorded, run scorers against them to catch regressions:

```python
from mlflow.genai.scorers import ConversationCompleteness, RelevanceToQuery

@scorer
def tool_recall(trace, expectations) -> Feedback:
    """Check if expected tools were used in the trace."""
    expected_tools = set(expectations.get("expected_tools", []))
    tool_spans = trace.search_spans(span_type="TOOL")
    actual_tools = {span.name.replace("tool_", "") for span in tool_spans}
    matched = expected_tools & actual_tools
    recall = len(matched) / len(expected_tools)
    return Feedback(value=recall, rationale=f"Expected: {expected_tools}, Found: {actual_tools}")

@scorer
def num_permission_block(trace) -> int:
    """Count how many times the agent hit a permission block."""
    count = 0
    for span in trace.search_spans(span_type="TOOL"):
        if span.outputs and "result" in span.outputs:
            result = span.outputs["result"]
            if "requires approval" in result.lower() or "was blocked." in result.lower():
                count += 1
    return count

traces = mlflow.search_traces(experiment_ids=["<experiment-id>"], max_results=20)

results = mlflow.genai.evaluate(
    data=traces,
    scorers=[
        tool_recall,
        num_permission_block,
        ConversationCompleteness(),
        RelevanceToQuery(),
    ],
)
```

This is especially powerful for skills and sub-agents that run unattended. You build the automation, define evaluation criteria, and MLflow tells you whether it is working reliably.

### Tip 3: MLflow MCP Server

Connect Claude Code to your MLflow tracking server so the agent can query your own data:

```json
{
  "mcpServers": {
    "mlflow-mcp": {
      "command": "uv",
      "args": ["run", "--with", "mlflow[mcp]>=3.5.1", "mlflow", "mcp", "run"],
      "env": {
        "MLFLOW_TRACKING_URI": "<MLFLOW_TRACKING_URI>"
      }
    }
  }
}
```

Add this to `.claude/settings.json`. Claude Code can now search traces, log feedback, query metrics, and manage experiments directly.

### Tip 4: MLflow Skills Package

Install official MLflow skills for Claude Code:

```bash
npx skills add mlflow/skills
```

Adds skills for: trace analysis, agent evaluation, metrics querying, debugging. Claude becomes a full MLflow expert without manual instruction.

### Tip 5: MLflow Assistant

MLflow Assistant embeds Claude Code directly in the MLflow UI. It shares the UI's current context — which traces, runs, and evaluations you are looking at — and can connect failing traces back to the actual code that produced them, suggest fixes, and set up evaluation pipelines tailored to your stack.

Uses your existing Claude Code subscription; no additional API keys or cost.

---

## 11. Business Applications {#business-applications}

*From the NisonCo 2026 business guide.*

### What Claude Code Enables for Businesses Without Large Engineering Teams

- Scaffold complete applications (back-end APIs to front-end interfaces) through conversational prompts
- Connect to proprietary systems through custom MCP servers that Zapier and Make.com do not support
- Build internal dashboards with Artifacts (interactive visualizations connected to your data)
- Run automated workflows that chain multiple operations with contextual decision-making, not just predetermined steps

### The MCP Integration Gap

Pre-built automation platforms cover standard SaaS integrations. Custom MCP servers cover everything else:

```
Zapier / Make.com:
  ✓ Slack, Google Workspace, Salesforce, Shopify, 1000s of SaaS tools
  ✗ Your internal ERP
  ✗ Legacy databases
  ✗ Vertical-specific software (seed-to-sale tracking, patient outcome databases)

Custom MCP Server:
  ✓ Any system with an API or queryable database
  ✓ Full control over what data Claude can access
  ✓ Audit trails that satisfy compliance requirements
  ✓ Granular permission control (read-only → write → admin, phased by trust)
```

Build pattern: define the data model → create the MCP server → configure access → let Claude build the interface layer.

### CLAUDE.md as an Employee Handbook

For business teams, CLAUDE.md is the agent's operating manual. Include:
- Team code review requirements
- Preferred libraries and frameworks
- Documentation standards
- Testing expectations
- Domain-specific terminology and business rules
- Format requirements for client deliverables

Check `.claude/settings.json` into source control. Every team member's Claude sessions follow the same standards automatically.

### ROI Measurement: What the Research Shows

| Study | Finding | Context |
|---|---|---|
| GitHub Copilot controlled trial (n=95) | 55% faster on scoped task | Building HTTP server in JavaScript, clear requirements |
| METR 2025 study | 19% slower for experienced developers | Complex tasks in mature repos with deep domain knowledge |

The lesson: gains are highly context-dependent. Simple, well-defined tasks with clear acceptance criteria show dramatic speedups. Complex refactoring in legacy codebases with extensive domain knowledge can slow teams down if they spend more time correcting AI-generated suggestions than writing code.

**Where it reliably adds value:**
- Automating repetitive data transformations
- Generating boilerplate code
- Building internal tools quickly
- Prototyping (idea to working tool in hours, not weeks)

**Where to be careful:**
- Complex refactoring of mature codebases with intricate domain logic
- Tasks where the overhead of reviewing AI output exceeds the time saved

### Agentic Workflow Architecture (Business Context)

Once you have persistent instructions and MCP integrations configured, you can chain multi-step workflows:

> "Take the feature requests from last week's user interviews, create GitHub issues with proper labels, update our roadmap spreadsheet, and draft a summary email for stakeholders."

This works because the agent has:
- **Context** (CLAUDE.md — knows your conventions, domain terminology)
- **Configuration** (settings.json — approved tools, model choices)
- **Connectivity** (MCP servers — can reach your systems)

The intelligence layer makes these workflows resilient rather than brittle. When the GitHub API rate-limits a bulk operation, Claude can pause and retry. When stakeholder emails bounce, it flags for human review. Predetermined automation scripts break; agentic workflows adapt.

---

## Cross-Reference: Where to Find Things

| Topic | File |
|---|---|
| `/loop` command (recurring tasks) | `05-workflows-and-automation.md` |
| Remote Control (web/mobile → local session) | `05-workflows-and-automation.md` |
| Channels (event-driven warm sessions) | `05-workflows-and-automation.md` |
| CI/CD integration (GitHub Actions, GitLab) | `05-workflows-and-automation.md` |
| Legacy codebase refactoring | `05-workflows-and-automation.md` |
| The Ralph Loop | `05-workflows-and-automation.md` |
| Hooks (all 8 event types) | `05-workflows-and-automation.md` |
| Orchestra Research Framework | `05-workflows-and-automation.md` |
| CLAUDE.md configuration | This file, sections 3, 6, 7 |
| Sub-agents and skills | This file, sections 4, 5, 6 |
| Multi-agent orchestration | This file, sections 7, 8 |
| Context management patterns | This file, sections 3, 8 |
| Python-specific setup | This file, section 6 |
| MLflow tracing and evaluation | This file, section 10 |
| Business use cases and ROI | This file, section 11 |
