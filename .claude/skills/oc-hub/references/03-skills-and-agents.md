# Skills and Agents: The Definitive Guide

## Table of Contents

1. [What Skills Are](#what-skills-are)
2. [Skill Format and Structure](#skill-format-and-structure)
3. [Progressive Disclosure Architecture](#progressive-disclosure-architecture)
4. [Skill Categories](#skill-categories)
5. [Writing Effective Skills](#writing-effective-skills)
6. [The Skill Lifecycle: Create, Test, Share, Improve](#the-skill-lifecycle)
7. [Subagent Patterns](#subagent-patterns)
8. [Agent Teams](#agent-teams)
9. [Real-World Examples by Domain](#real-world-examples-by-domain)
10. [The Plugin Ecosystem](#the-plugin-ecosystem)
11. [Skills vs Other Approaches](#skills-vs-other-approaches)
12. [Security Considerations](#security-considerations)

---

## What Skills Are

A skill is a folder containing a `SKILL.md` file and optional supporting resources that teaches Claude how to handle specific tasks or workflows. Skills are loaded progressively and activate automatically when Claude determines the current task matches the skill's purpose.

The core problem skills solve: AI agents have no memory between sessions. Without skills, you re-explain your preferences, processes, and domain expertise in every conversation. Skills encode that knowledge once. Every future conversation picks it up automatically — no pasting, no repeating.

**Agent Skills** is an open standard launched by Anthropic in late 2025. It is not Claude-specific. The same skill format works across Claude Code, OpenAI Codex CLI, Gemini CLI, Cursor, GitHub Copilot, JetBrains Junie, and more. Skills you write are portable across all platforms that have adopted the standard.

### Two Kinds of Skills

There is an important distinction that changes how you think about building and choosing skills:

**Capability Uplift skills** give Claude abilities it does not have on its own. Before the skill, Claude cannot do the task reliably. After installing it, Claude has new capabilities. Examples:
- Web scraping with the Firecrawl skill (Claude cannot do reliable web scraping at scale without it)
- Creating real PDF, DOCX, XLSX, and PPTX files (Claude generates text descriptions without it; the skill executes Python scripts to produce actual files)
- Running browser tests through Playwright
- Running static analysis tools like CodeQL and Semgrep

**Encoded Preference skills** are different. Claude already knows how to do the underlying task. The skill encodes your team's specific way of doing it. Examples:
- NDA review processes
- Weekly status update formats
- Commit message conventions
- Code review checklists
- Design aesthetic direction (the Frontend Design skill bans overused fonts and forces bold aesthetic choices)

Both types load progressively and trigger contextually. Knowing which kind you need changes how you think about building or choosing skills.

---

## Skill Format and Structure

A skill is a directory with a specific layout:

```
your-skill-name/
├── SKILL.md          # Required — main instructions with YAML frontmatter
├── scripts/          # Optional — executable code (Python, Bash, etc.)
│   ├── process_data.py
│   └── validate.sh
├── references/       # Optional — documentation loaded on demand
│   ├── api-guide.md
│   └── examples/
└── assets/           # Optional — templates, fonts, icons used in output
    └── report-template.md
```

### Critical Rules

- `SKILL.md` must be named exactly that — case-sensitive. `SKILL.MD`, `skill.md`, and other variants are not recognized.
- The skill folder name must use kebab-case: `notion-project-setup` is correct. `Notion Project Setup`, `notion_project_setup`, and `NotionProjectSetup` are not.
- Do not include a `README.md` inside the skill folder. All documentation goes in `SKILL.md` or `references/`. A repo-level `README.md` is fine for human readers, but it must not be inside the skill folder itself.
- Skill names must not start with `claude` or `anthropic` — these are reserved.

### Installation Locations

```
# Personal skills — available across all your projects
~/.claude/skills/<skill-name>/SKILL.md

# Project skills — shared with everyone who clones the repo
.claude/skills/<skill-name>/SKILL.md

# Plugin skills — distributed via the plugin system
<plugin-dir>/skills/<skill-name>/SKILL.md
```

To install from GitHub:

```bash
# Using the skills CLI
npx skills add https://github.com/anthropics/skills --skill frontend-design

# Using Claude Code's plugin system
/plugin marketplace add anthropics/skills
/plugin install frontend-design@anthropics/skills

# Manual — copy skill folder to skills directory
cp -r skills/my-skill ~/.claude/skills/my-skill
```

### The YAML Frontmatter

The frontmatter is the most critical part of any skill. It is what Claude reads to decide whether to load the skill at all.

**Minimal required format:**

```yaml
---
name: your-skill-name
description: What it does. Use when user asks to [specific phrases].
---
```

**Full format with all optional fields:**

```yaml
---
name: skill-name-in-kebab-case
description: What it does and when to use it. Include specific trigger phrases.
license: MIT
allowed-tools: "Bash(python:*) Bash(npm:*) WebFetch"
metadata:
  author: Company Name
  version: 1.0.0
  mcp-server: server-name
  category: productivity
  tags: [project-management, automation]
  documentation: https://example.com/docs
---
```

**Security restrictions in frontmatter:**
- No XML angle brackets (`<` or `>`) — frontmatter appears in Claude's system prompt and malicious content could inject instructions
- No code execution in YAML (uses safe YAML parsing)
- `description` must be under 1024 characters

**Frontmatter control options:**
- `disable-model-invocation: true` — Only you can invoke this skill; Claude will not trigger it automatically. Use for anything with side effects.
- `user-invocable: false` — Only Claude can invoke it (background knowledge). Use for conventions you want Claude to follow automatically.
- `allowed-tools` — Restrict which tools Claude can use. Useful for read-only research skills.
- `context: fork` — Run in an isolated subagent. Good for research tasks that should not pollute your main conversation.
- `agent` — Which subagent type to use (`Explore`, `Plan`, `general-purpose`).
- `argument-hint` — Describes expected arguments for slash command invocation.

---

## Progressive Disclosure Architecture

Skills use a three-level loading system that keeps context efficient across dozens of installed skills:

**Layer 1 — Cover page (always loaded, ~100 tokens per skill):**
The YAML frontmatter. Claude reads this for every installed skill at startup to know when to activate each one. This is roughly the name and description. Total context cost: approximately 100 tokens per installed skill. With 20 skills installed, that is about 2,000 tokens — well within budget.

**Layer 2 — Full instructions (loaded only when relevant, keep under 500 lines):**
The body of `SKILL.md`. Only loads when Claude determines the skill is relevant to your current task. Recommended maximum of 5,000 words or about 500 lines.

**Layer 3 — Supporting files (loaded on demand, no hard limit):**
Everything in `references/`, `scripts/`, and `assets/`. Claude pulls these in only when the instructions direct it to. Scripts execute directly without being loaded into the context window at all, which saves tokens and improves accuracy.

**Practical consequence:** You can have 17+ skills installed simultaneously and Claude will only load the one or two relevant to your current task. The others wait silently.

**The golden rule of skill authoring:** Keep `SKILL.md` under 200 lines as a table of contents that tells Claude where to look, not a dump of everything it might need. Move detailed documentation to `references/` and link to it from `SKILL.md`.

---

## Skill Categories

Anthropic has identified three common use case categories from early adopter patterns:

### Category 1: Document and Asset Creation

Used for creating consistent, high-quality output — documents, presentations, apps, designs, code.

**Characteristics:**
- Embedded style guides and brand standards
- Template structures for consistent output
- Quality checklists before finalizing
- No external tools required — uses Claude's built-in capabilities

**Examples:** `frontend-design`, `pdf`, `docx`, `pptx`, `xlsx`, `canvas-design`, `algorithmic-art`

### Category 2: Workflow Automation

Used for multi-step processes that benefit from consistent methodology, including coordination across multiple MCP servers.

**Characteristics:**
- Step-by-step workflow with validation gates
- Templates for common structures
- Built-in review and improvement suggestions
- Iterative refinement loops

**Examples:** `skill-creator`, `daily-planning`, `prd-to-issues`, `deploy`

### Category 3: MCP Enhancement

Used to add workflow guidance on top of the tool access an MCP server provides.

**Characteristics:**
- Coordinates multiple MCP calls in sequence
- Embeds domain expertise
- Provides context users would otherwise need to specify
- Error handling for common MCP issues

**Examples:** `pulumi-best-practices`, `sentry-code-review`, `pg-aiguide`

### The Kitchen and Recipes Analogy

MCP is the kitchen — tools, ingredients, equipment. Skills are the recipes — step-by-step instructions on how to create something valuable. MCP provides capability; skills provide intelligence. You need both. The process alone is theoretical, and tools without a process just sit in the garage.

| MCP (Kitchen) | Skills (Recipes) |
|---------------|-----------------|
| Connects tools | Teaches how to use those tools |
| Provides real-time data access | Packages workflows and best practices |
| Solves "can it do this?" | Solves "how to do it best" |

---

## Writing Effective Skills

### The Description Field

The description field is the single most important part of any skill. It is what Claude uses to decide whether to load your skill. Claude errs on the side of not triggering rather than triggering incorrectly. With vague descriptions, auto-trigger accuracy drops to around 20%. With specific, well-written descriptions, accuracy exceeds 90%.

A good description answers two questions:
1. What this skill does — so Claude knows its purpose
2. What the user will say — specific trigger phrases

**Good descriptions:**

```yaml
description: Daily work planning workflow. Use when the user says
"plan my day", "daily planning", "start work", or "morning routine".
```

```yaml
description: Analyzes Figma design files and generates developer handoff
documentation. Use when user uploads .fig files, asks for "design specs",
"component documentation", or "design-to-code handoff".
```

```yaml
description: GRPO training skill based on external vLLM server using ms-swift.
Usage scenarios: (1) When performing GRPO training with the vLLM server running
on a separate GPU, (2) When encountering errors related to vllm_skip_weight_sync,
(3) When encountering OpenAI API response parsing errors. Verified on gemma-3-12b-it.
```

**Bad descriptions:**

```yaml
description: Helps with projects.         # Too vague, no trigger phrases
description: Creates sophisticated documentation systems.  # Missing triggers
description: Implements the Project entity model.          # Too technical
```

**Tips:**
- List multiple trigger phrase variations — Claude under-triggers, so more is safer
- Include specific error messages or technical terms you want Claude to match on
- Mention file types if relevant (`.fig`, `.csv`, `.pdf`)
- State what the skill outputs and where it has been tested

### Writing the Instructions Body

After the frontmatter, write instructions in Markdown. Recommended structure:

```markdown
---
name: your-skill
description: [well-crafted description]
---

## Your Skill Name

## Step 1: [First Major Step]
Clear explanation of what happens here.

Example:
```bash
python scripts/fetch_data.py --project-id PROJECT_ID
```
Expected output: [describe what success looks like]

## Step 2: [Next Step]
...

## Examples

**Example 1: [common scenario]**
User says: "Set up a new marketing campaign"
Actions:
1. Fetch existing campaigns via MCP
2. Create new campaign with provided parameters
Result: Campaign created with confirmation link

## Troubleshooting

**Error: [Common error message]**
- Cause: [Why it happens]
- Solution: [How to fix]
```

### Explain Why, Not Just What

The most important principle from Anthropic's official skill-building guide:

> Try to explain to the model why things are important in lieu of heavy-handed musty MUSTs.

Replace commands with reasons:

**Instead of:**
```
ALWAYS show command contents before executing. NEVER execute directly.
```

**Write:**
```
Show command contents before executing, because users need to verify safety.
Executing without confirmation could cause irreversible damage.
```

With reasons, Claude can generalize to situations the rules do not cover. With just rules, Claude is stuck when it encounters an edge case. The only exception is mechanical formatting requirements — those can stay as hardcoded specs.

### Skill Design Patterns

Five patterns that appear across effective skills:

| Pattern | Description | Example |
|---------|-------------|---------|
| Sequential execution | Ordered steps with dependencies | Daily planning: review yesterday → check weekly goals → create daily note |
| Cross-tool orchestration | Chain multiple tools, data flows between systems | Project init: create GitHub repo → generate folders → set up CI/CD → notify Slack |
| Iterative refinement | Draft, check, revise, check again until standards are met | Content editing: first draft → style check → quality review → loop back if fails |
| Conditional branching | Same goal, different paths based on context | SEO research: look up keywords, analyze competitors, or map industry landscape |
| Domain-specific intelligence | Encode expertise, not just tool operations | Code review: naming conventions, error handling principles, test coverage — write once, apply always |

Most effective skills combine multiple patterns.

---

## The Skill Lifecycle

### Step 1: Create

**The fastest approach — use the official skill-creator:**

The `skill-creator` skill (available at `claude.com/plugins/skill-creator` or installable via `npx skills add https://github.com/anthropics/skills --skill skill-creator`) walks through an interactive Q&A that generates a complete skill directory.

```
"Use the skill-creator to help me build a skill for running database migrations safely"
"Help me create a skill for our team's code review checklist"
"Build a skill that enforces our commit message format"
```

The skill-creator can also:
- Auto-generate test cases and verify trigger accuracy
- Auto-optimize descriptions and instructions based on test results
- Run A/B tests between two versions of a skill
- Track benchmark scores across iterations

**Manual creation — when you already know what you want:**

First iterate on the task in conversation until Claude gets it right. Then extract the successful approach:

```
"Turn what we just did into a skill."
```

Claude auto-generates the `SKILL.md` and folder structure. This leverages Claude's in-context learning and provides faster signal than designing from scratch.

**Refactoring community skills:**

Most community skills have useful content but poor structure — 1,000-line `SKILL.md` files with no progressive disclosure. The fix:

1. Install the skill: `npx skills add author/repo --skill skill-name`
2. Open Claude Code and say: "Take the [skill-name] skill and use the skill-creator skill to refactor it. I want the SKILL.md to be max 200 lines and all reference information moved to the references folder."

This typically reduces a 400-line `SKILL.md` to under 150 lines while creating proper reference files. The result loads 60% less context on activation.

### Step 2: Test

Three testing areas for production-quality skills:

**Triggering tests — does the skill load at the right times?**

```
Should trigger:
- "Help me set up a new ProjectHub workspace"
- "I need to create a project in ProjectHub"
- "Initialize a ProjectHub project for Q4 planning"

Should NOT trigger:
- "What's the weather in San Francisco?"
- "Help me write Python code"
- "Create a spreadsheet" (unless this skill handles spreadsheets)
```

Target: triggers on 90%+ of relevant queries.

**Debugging undertriggering:** Ask Claude: "When would you use the [skill name] skill?" Claude will quote the description back. Adjust based on what is missing.

**Functional tests — does the skill produce correct outputs?**

Run the same request 3-5 times. Compare outputs for structural consistency and quality. Can a new user accomplish the task on first try with minimal guidance?

**Using the built-in eval system (skill-creator v2+):**

```
"Run a new test using the skill-creator evals. Optimize for making sure my content
follows the content-type-optimization pattern."
```

The eval system runs a task through 5-10 parallel agent instances, scores each against your criteria (keep to 3-5 criteria per run), and produces a benchmark report with pass rates, token usage, and timing. Use A/B testing to determine whether reference files are improving quality or just costing tokens.

### Step 3: Add Business Context

A skill without your business context is generic. The most valuable skills have your specific information embedded:

```
references/
├── brand-voice.md       # Tone, style examples, words to avoid
├── icp.md               # Ideal customer profile
├── positioning.md       # How you differentiate from competitors
└── content-pillars.md   # Core topics and themes
```

In `SKILL.md`, reference this context only when it is needed for a specific step:

```markdown
## Step 2: Craft the Copy

Before writing, load `references/positioning.md` for citation-worthy framing
that differentiates the brand. Load `references/icp.md` to tailor messaging
to our specific audience segment.
```

The skill loads context progressively — only what each step needs, not everything at once.

### Step 4: Build a Learning Loop

Skills can improve with every use through a feedback and learnings system:

In `SKILL.md`, add a rules and learnings section:

```markdown
## Rules and Learnings

Rules are updated from session feedback. Always read this section before executing.

Current learnings:
- Articles that open with a direct answer to the search query in paragraph 1
  get picked up in AI search more quickly (observed 2025-11-12)
- Comparison tables mid-article increase time on page (observed 2025-11-19)
```

Add a wrap-up skill that runs at the end of each session to capture new learnings:

```markdown
After completing a task, review the output against quality criteria.
If you identify specific patterns that improved results, append them to
references/learnings.md with the date observed.
```

**Keep the learnings file pruned.** Review weekly and strip anything that no longer contributes to quality. An unbounded learnings file becomes its own context problem.

### Step 5: Share and Distribute

**Personal use:** Skills in `~/.claude/skills/` are available across all projects.

**Team use:** Skills in `.claude/skills/` inside a repository are shared with everyone who clones it. Commit them to git.

**Community use (GitHub):**
1. Create a public repo with your skill directories
2. Add a repo-level `README.md` with installation instructions (the README goes in the repo root, not inside skill folders)
3. Make it installable: `npx skills add yourusername/your-skills-repo --skill skill-name`

**Plugin distribution:**
To make skills discoverable via the plugin marketplace, add a `.claude-plugin/plugin.json` to your repo:

```json
{
  "name": "your-skill-collection",
  "version": "1.0.0",
  "description": "Description for marketplace listing",
  "author": {
    "name": "Your Name"
  },
  "skills": "./skills",
  "repository": "https://github.com/yourusername/your-skills-repo"
}
```

Users install via:
```
/plugin marketplace add yourusername/your-skills-repo
/plugin install all-skills@your-skills-repo
```

**API distribution:**
For programmatic deployment, the `/v1/skills` endpoint allows managing skills and adding them to Messages API requests via the `container.skills` parameter. Organization admins can deploy skills workspace-wide (shipped December 2025).

---

## Subagent Patterns

Subagents are separate Claude Code instances spawned by your main instance to do work in isolation.

**Key characteristics:**
- The subagent's context is completely isolated from the main agent
- The subagent gets only what the main agent explicitly sends it
- The subagent returns results when done — it does not share an ongoing context
- Subagents do not persist between invocations
- Each subagent loads your `CLAUDE.md` and MCP servers, but not your conversation history

**In SKILL.md, invoke a subagent:**

```markdown
## Step 3: Research Phase

Spawn a subagent with `context: fork` to investigate the following without
polluting the main conversation context:
1. Search the codebase for all usages of the deprecated API
2. Document each call site and its surrounding context
3. Return a structured report of findings

Do not make any changes in the subagent — read-only investigation only.
```

**Built-in subagent skills** (from `obra/superpowers`):

The `/execute-plan` skill spawns fresh subagents per task from a written plan. Each subagent:
1. Gets a two-stage review (spec compliance, code quality)
2. Runs in isolation, preventing context drift
3. Reports back to the orchestrator before the next task begins

**When to use subagents:**
- Tasks that do not need shared context with your main conversation
- Research tasks where you want bias isolation (each subagent investigates independently)
- Parallel work on completely independent files or concerns
- Any side effect that you want cordoned off from your main session

**When not to use subagents:**
- Tasks that need deep context from your current session (pass it explicitly in the task spec instead)
- Sequential tasks where each step depends on the previous output

---

## Agent Teams

Agent teams are a distinct pattern from simple subagent spawning. They are orchestrated ensembles where teammates communicate with each other, not just with the orchestrator.

### Subagents vs Agent Teams

| | Subagents | Agent Teams |
|---|---|---|
| Context isolation | Complete — subagent gets only what it is sent | Partial — teammates share messages with each other |
| Communication | One-way reporting back to orchestrator | Multi-directional messaging between teammates |
| Coordination | Orchestrator delegates tasks, waits for results | Teammates collaborate in real-time |
| Best for | Isolated parallel execution | Cross-domain work requiring collaboration |
| Cost | Lower — each subagent is scoped | Higher — scales linearly with teammate count |

### How Agent Teams Work

1. The orchestrator creates a task list and spawns teammates
2. Teammates receive tasks and send messages to each other (not full context, just messages)
3. You can address the orchestrator or any individual teammate
4. Teammates auto-idle when their work is done and shut down automatically
5. The orchestrator notifies you when the team completes

The context sharing is message-based, not full context replication. If a teammate needs more context, tell the orchestrator to embed additional context pointers in the task specifications.

### Setting Up Agent Teams

Enable experimental agents in settings (this is still an experimental feature). Define your team in natural language:

```
"Create a performance agent team: one specializing in UI performance (looking for
jank and rendering issues), one specializing in error debugging and log analysis,
and one focused on pixel-perfect UX quality review."
```

To assign specific models per teammate (useful for cost control):

```
"For the agent team: the debugger should run on Opus, the UI perf agent on Sonnet,
and the UX quality agent on Haiku."
```

### Agent Team Best Practices

**Start small:** 3 teammates is often the optimal team size. Tokens scale linearly with team members. More than 3-4 agents frequently adds coordination overhead without proportional benefit.

**Plan before you deploy:** Agent teams require a plan. If you prefer diving straight into execution, agent teams will frustrate you. Use plan mode first, define clear tasks, then spawn the team.

**Avoid file conflicts:** Do not have multiple agents working on the same files simultaneously unless you are using git worktrees. Front-end one, front-end two, and front-end three working on the same components will create merge conflicts.

**Use agent teams for cross-domain work:** The clearest use cases:
- Frontend agent + backend agent + architecture agent on full-stack features
- Researcher + writer + editor for long-form content
- Security agent + performance agent + test coverage agent for parallel code review
- iOS parity agent + Android implementation agent for cross-platform feature work

**Competing hypothesis debugging:** Spawn one agent per theory to investigate in parallel. Because their contexts are isolated, each investigates with fresh eyes rather than being biased by the previous agent's findings. The orchestrator synthesizes all reports at the end.

**Keep tasks batch-sized:** Each round of work should be 5-6 focused tasks per agent, not 30 tasks all at once. Kick them off, review, then start the next batch.

**Guard rails:** The team lead occasionally starts implementing things directly rather than delegating. If this happens, redirect: "Stop, delegate this to your team members and wait for them to complete their tasks."

### Agent Team Hooks

Agent teams expose additional lifecycle hooks:
- `teammate-idle` — fires when a teammate has no more tasks
- `task-complete` — fires when a task finishes

These can trigger external notifications (Slack, Jira, Notion updates) or automated quality gates.

### Three-Tier Model Strategy for Agent Teams

From the `wshobson/agents` ecosystem, a practical model assignment strategy:

| Tier | Model | Use For |
|------|-------|---------|
| Tier 1 | Opus | Critical architecture, security, ALL code review, production coding |
| Tier 2 | Inherit | Complex tasks — user chooses the model for this tier at session start |
| Tier 3 | Sonnet | Support agents (docs, testing, debugging) |
| Tier 4 | Haiku | Fast operational tasks (SEO, deployment, simple lookups) |

Pattern: Opus (architecture) → Sonnet (development) → Haiku (deployment)

---

## Real-World Examples by Domain

### Engineering and DevOps

**Pulumi infrastructure (dirien/claude-skills):**
```bash
npx skills add https://github.com/dirien/claude-skills --skill pulumi-typescript
```
Teaches Claude Pulumi with TypeScript, ESC secrets management, OIDC instead of hardcoded access keys, ComponentResource patterns, and proper output structuring. Stops Claude from creating resources inside `apply()` callbacks (which breaks preview), enforces `pulumi preview` before deployment.

**Pulumi official skills (pulumi/agent-skills):**
```bash
npx skills add https://github.com/pulumi/agent-skills --skill pulumi-esc
npx skills add https://github.com/pulumi/agent-skills --skill pulumi-best-practices
```
`pulumi-esc` teaches the difference between `pulumi env get`, `pulumi env open`, and `pulumi env run`. Sets up OIDC for dynamic credentials. `pulumi-best-practices` stops the mistakes that burn you in production.

**Monitoring:**
```bash
npx skills add https://github.com/jeffallan/claude-skills --skill monitoring-expert
```
Without this skill, Claude deploys a static website and forgets monitoring. With it, Claude asks about error rate thresholds, suggests CloudWatch alarms, and creates SNS topics for alerts before writing infrastructure code.

**Kubernetes:**
```bash
npx skills add https://github.com/jeffallan/claude-skills --skill kubernetes-specialist
```
Returns deployments with `runAsNonRoot: true`, resource requests and limits, liveness/readiness probes, and pod disruption budgets — not just "something that runs."

**GitOps, CI/CD, cost, SRE:**
```bash
npx skills add https://github.com/wshobson/agents --skill gitops-workflow
npx skills add https://github.com/wshobson/agents --skill github-actions-templates
npx skills add https://github.com/wshobson/agents --skill cost-optimization
npx skills add https://github.com/wshobson/agents --skill sre-engineer
npx skills add https://github.com/jeffallan/claude-skills --skill devops-engineer
```

**Security:**
```bash
npx skills add https://github.com/wshobson/agents --skill k8s-security-policies
npx skills add trailofbits/skills    # CodeQL and Semgrep static analysis
```
Trail of Bits security skills encode the workflows they actually use for professional security audits — not checklists.

**Incident response:**
```bash
npx skills add https://github.com/wshobson/agents --skill incident-runbook-templates
```
Generates runbooks with a four-level severity model (SEV1-SEV4), escalation decision trees, `kubectl` commands for Kubernetes recovery, and SQL procedures for PostgreSQL troubleshooting. Treat outputs as a first draft that gets you to 60% in minutes.

**Python refactoring (l-mb/python-refactoring-skills):**

Eight modular skills that work together:

| Skill | Purpose | Key Tools |
|-------|---------|-----------|
| `py-refactor` | Orchestrates comprehensive refactoring | All tools |
| `py-security` | Detect and fix security vulnerabilities | bandit, ruff |
| `py-complexity` | Reduce cyclomatic/cognitive complexity | radon, lizard, wily |
| `py-test-quality` | Improve coverage and test effectiveness | pytest-cov, mutmut |
| `py-code-health` | Remove dead code and duplication | vulture, pylint |
| `py-modernize` | Upgrade tooling and syntax | uv, pyupgrade |
| `py-quality-setup` | Configure linters and type checkers | ruff, mypy |
| `py-git-hooks` | Set up automated quality checks | pre-commit |

Install:
```bash
git clone https://github.com/l-mb/python-refactoring-skills.git
./scripts/install-symlinks.sh
```

### Frontend Development

**Frontend Design (anthropics/skills):**
```bash
npx skills add https://github.com/anthropics/skills --skill frontend-design
```
Explicitly bans overused fonts (Inter, Roboto, Arial, Space Grotesk). Forces Claude to commit to a specific visual direction — brutalist, maximalist, retro-futuristic, editorial — before writing any code. 110k+ weekly installs. Encoded Preference skill.

**Vercel Web Design Guidelines (vercel-labs/agent-skills):**
```bash
npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines
```
Fetches the latest Web Interface Guidelines and checks your code against 100+ rules — ARIA attributes, visible focus states, labeled inputs, touch target sizes, reduced-motion support, semantic HTML. Output format: `file:line` findings you can act on immediately.

**Vercel React Best Practices:**
```bash
npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-react-best-practices
```
57 rules across 8 categories, ordered by actual impact. Addresses request waterfalls before micro-optimizations. Stops Claude from reaching for `useMemo` when the real bottleneck is a barrel file importing an entire icon library.

**Vercel Composition Patterns:**
```bash
npx skills add https://github.com/vercel-labs/agent-skills --skill composition-patterns
```
Replaces boolean prop proliferation (`isCompact`, `showHeader`, `isRounded`, `hasBorder`) with compound components, state decoupling via provider interfaces, and explicit variant components.

**Browser automation (SawyerHood/dev-browser):**
```bash
/plugin marketplace add sawyerhood/dev-browser
/plugin install dev-browser@sawyerhood/dev-browser
```
Full Playwright API in a sandboxed QuickJS runtime. Persistent named pages across scripts. Benchmarks show 100% success rate at 3m 53s and $0.88 cost per task — significantly faster and cheaper than alternatives.

```javascript
const page = await browser.getPage("main");
await page.goto("https://example.com");
const snapshot = await page.snapshotForAI({ track: true });
```

**Webapp Testing (anthropics/skills):**
```bash
npx skills add https://github.com/anthropics/skills --skill webapp-testing
```
Claude controls a real browser via Playwright to test your local app during development. Catches JavaScript errors, timing issues, and interaction problems that static analysis misses.

### Document Workflows

**Official document skills (anthropics/skills):**
```bash
npx skills add https://github.com/anthropics/skills --skill pdf
npx skills add https://github.com/anthropics/skills --skill docx
npx skills add https://github.com/anthropics/skills --skill xlsx
npx skills add https://github.com/anthropics/skills --skill pptx
```
These execute Python scripts to produce actual files — not text descriptions. Chain them: extract tables from a PDF, process in Excel, output a formatted Word report, summarize in a PowerPoint.

### Research and ML

**AI Research Skills Library (Orchestra-Research/AI-Research-SKILLs):**
86 skills covering the full AI research lifecycle:
- Autoresearch, Ideation, ML Paper Writing
- Model Architecture, Fine-Tuning, Post-Training, Distributed Training
- Optimization, Inference Serving, Evaluation
- RAG, Prompt Engineering, MLOps, Observability
- Safety and Alignment, Agents, Multimodal, Emerging Techniques

Each skill provides expert-level guidance for specific frameworks: Megatron-LM, vLLM, TRL, ms-swift, and many more.

**Team Knowledge Registry (Sionic AI pattern):**

A skills-based system for capturing experimental learnings as team memory:

Repository structure:
```
your-org/research-skills/
├── plugins/
│   └── training/
│       └── your-first-experiment/
│           ├── .claude-plugin/
│           │   └── plugin.json
│           ├── skills/your-first-experiment/
│           │   └── SKILL.md
│           ├── references/
│           │   ├── experiment-log.md
│           │   └── troubleshooting.md
│           └── scripts/
├── templates/
│   └── experiment-skill-template/
└── CLAUDE.md
```

The `CLAUDE.md` at the root defines two custom commands:

```markdown
## Commands

### /advise
Search the skills registry for relevant experiments before starting new work.
1. Read the user's goal
2. Search plugins/ for related skills by scanning description fields
3. Summarize relevant findings: what worked, what failed, recommended parameters

### /retrospective
Save learnings from the current session as a new skill.
1. Summarize key findings from the conversation
2. Create a new plugin folder using templates/experiment-skill-template/
3. Fill in SKILL.md with: goal, what worked, what failed, final parameters
4. Create a branch and open a PR to main

## Rules
- Every skill needs a specific description field with trigger conditions
- Always include a "Failed Attempts" table
- Include exact hyperparameters, not vague advice
```

The **Failed Attempts table** is the most referenced part of any research skill:

```markdown
| Attempt | Why it Failed | Lesson Learned |
|---------|---------------|----------------|
| Execution without `vllm_skip_weight_sync` | 404 `/update_flattened_params/` error | `--vllm_skip_weight_sync true` is mandatory when using `vllm serve` |
| Running vLLM without `--served-model-name` | 404 Model `default` not found | Must add `--served-model-name default` to vLLM server args |
```

GitHub Actions validate PRs touching the `plugins/` folder and regenerate `marketplace.json` on merge.

### Marketing and Content

**Corey Haines' Marketing Skills (coreyhaines31/marketingskills):**
```bash
# All 32 skills
npx skills add coreyhaines31/marketingskills

# Select skills
npx skills add coreyhaines31/marketingskills --skill page-cro copywriting seo-audit
```

32 skills across the full marketing funnel:

| Skill | What it does |
|-------|-------------|
| `page-cro` | Conversion optimization for any marketing page |
| `copywriting` | Homepage, landing page, and feature copy |
| `seo-audit` | Technical and on-page SEO review |
| `ai-seo` | Optimization for AI search (AEO, GEO, LLMO) |
| `email-sequence` | Automated lifecycle email flows |
| `cold-email` | B2B cold outreach and follow-up sequences |
| `ab-test-setup` | Experiment design and implementation |
| `analytics-tracking` | GA4 and event tracking setup |
| `churn-prevention` | Cancel flows, save offers, dunning |

Requires populating a `product-marketing-context` file with your specific product information before skills produce useful output.

### Engineering Workflow Skills (from the field)

A developer-focused set of skills for structured software delivery:

**`grill-me` skill** (3 sentences):
```markdown
Interview me relentlessly about every aspect of this plan until we reach
a shared understanding. Walk down each branch of the design tree, resolving
dependencies between decisions one by one. If a question can be answered by
exploring the codebase, explore the codebase instead.
```
Forces the AI to interview you about every part of a design before touching code. Sessions of 16-50 questions are normal for complex features. Skills do not have to be long to be impactful — the right words at the right time matter more than volume.

**`write-prd` skill:** Takes a fully explored design and writes it as a structured GitHub issue with problem statement, user stories, and implementation decisions. References the `grill-me` flow for the interview step.

**`prd-to-issues` skill:** Breaks a PRD into vertical slices — thin cuts through all integration layers that flush out unknown unknowns quickly. Establishes blocking relationships between issues so parallel agents can pick up independent work simultaneously.

**`tdd` skill:** Enforces red-green-refactor discipline. Prompts the agent to confirm interface changes first, design for testability, write one failing test at a time, then write code to pass the test. Includes guidance on deep modules and module boundaries. The most consistent way to improve agent code quality.

**`improve-codebase-architecture` skill:** Explores the codebase to surface confusions, presents numbered deepening opportunities, spawns 3+ subagents in parallel each producing a radically different interface design for the selected module, then synthesizes a recommendation. Creates a refactor RFC as a GitHub issue.

---

## The Plugin Ecosystem

The `claude-code-plugin` GitHub topic has over 1,000 public repositories. Key collections:

### Large Community Collections

**wshobson/agents (32k stars):** 72 focused plugins, 112 specialized agents, 146 agent skills, 16 workflow orchestrators, 79 development tools. Install what you need:
```bash
/plugin marketplace add wshobson/agents
/plugin install python-development
/plugin install kubernetes-operations
/plugin install full-stack-orchestration
/plugin install agent-teams
```

**alirezarezvani/claude-skills (6.3k stars):** 205 skills across 9 domains — engineering, DevOps, marketing, compliance, C-level advisory. Converts to 11 tools (Claude Code, Codex, Gemini CLI, Cursor, Aider, etc.):
```bash
/plugin marketplace add alirezarezvani/claude-skills
/plugin install engineering-skills@claude-code-skills
/plugin install marketing-skills@claude-code-skills
/plugin install c-level-skills@claude-code-skills
```

**obra/superpowers (40.9k stars):** Composable development lifecycle framework:
```bash
/plugin marketplace add obra/superpowers-marketplace
```
Key skills: `/brainstorm` (structured design Q&A), `/write-plan` (breaks designs into 2-5 minute tasks with exact file paths), `/execute-plan` (dispatches fresh subagents per task), `using-git-worktrees`, `test-driven-development`, `systematic-debugging`.

**travisvn/awesome-claude-skills (9.5k stars):** Curated list of skills and resources. Good discovery resource.

**Orchestra-Research/AI-Research-SKILLs (5.4k stars):** 86 AI research skills covering the full research lifecycle.

### Specialized Skills Worth Knowing

**adversarial-spec (zscole, 513 stars):** Iteratively refines product specifications by debating between multiple LLMs (GPT, Gemini, Grok, etc.) until all models reach consensus. Claude is an active participant, not just an orchestrator.
```bash
/plugin marketplace add zscole/adversarial-spec
/plugin install adversarial-spec
/adversarial-spec "Build a rate limiter service with Redis backend"
```

**claude-mem (thedotmack, 39.4k stars):** Automatically captures everything Claude does during sessions, compresses it with AI, and injects relevant context into future sessions.

**SawyerHood/dev-browser (3.9k stars):** Full Playwright API for browser automation inside a sandboxed runtime.

**pg-aiguide (timescale, 1.6k stars):** MCP server and Claude plugin for PostgreSQL skills — helps AI coding tools generate better PostgreSQL code.

**claude-code-safety-net (kenryu42, 1.2k stars):** Acts as a safety net, catching destructive git and filesystem commands before they execute.

**arscontexta (agenticnotetaking, 2.8k stars):** Generates individualized knowledge systems from conversation — a "second brain" as markdown files you own.

**adversarial-spec (zscole):** Multi-LLM spec refinement with consensus loop, preserve-intent mode, session persistence, and cost tracking.

### Skills Discovery

**skills.sh** — Vercel-maintained searchable directory of published skills. Search by category, author, or install count. Fastest way to find skills without digging through GitHub repos.

**ClawHub** — Third-party marketplace. Note: Snyk research found 13.4% of skills on ClawHub had critical vulnerabilities. Scan with `uvx mcp-scan@latest --skills` before installing anything from there.

---

## Skills vs Other Approaches

| Tool | Best For |
|------|---------|
| Skills | Reusable procedural knowledge across conversations |
| Prompts | One-time instructions and immediate context |
| Projects | Persistent background knowledge within workspaces |
| Subagents | Independent task execution with specific permissions |
| MCP | Connecting Claude to external data sources and APIs |

**Key insight:** If you find yourself typing the same prompt repeatedly across multiple conversations, it is time to create a skill.

| Feature | Skills | System Prompts |
|---------|--------|----------------|
| Structure | Folder with YAML frontmatter, instructions, scripts | Plain text |
| Reusability | Version-controlled, shareable, composable | Copy-paste, conversation-specific |
| Loading | On-demand (only when relevant) | Always in context |
| Maintenance | Centralized updates | Manual updates per conversation |
| Composability | Multiple skills stack automatically | Manual combination |
| Token cost | ~100 tokens until loaded | Full text always loaded |

**Skills vs MCP:**

| Feature | Skills | MCP |
|---------|--------|-----|
| Purpose | Task-specific expertise and workflows | External data and API integration |
| Portability | Same format everywhere | Requires server configuration |
| Code execution | Can include executable scripts | Provides tools and resources |
| Token efficiency | 30-100 tokens until loaded | Varies by implementation |
| Best for | Repeatable tasks, document workflows | Database access, API integrations |

Skills and MCP work together: use MCP for what Claude needs access to; use skills for how Claude should use that access.

---

## Security Considerations

Skills run with the same permissions as your AI agent. A malicious skill can exfiltrate credentials, download backdoors, or disable safety mechanisms — and it will look like your agent doing it.

**Snyk research (February 2026)** scanned 3,984 skills from public registries:
- 13.4% had critical-level vulnerabilities
- 76 confirmed malicious payloads
- Attack techniques included: base64-encoded commands that steal AWS credentials, skills directing you to download password-protected executables from attacker infrastructure, jailbreak attempts
- 91% of malicious skills combine code-level malware with prompt injection
- 17.7% of skills on ClawHub pull from third-party URLs at runtime (behavior can change after installation)

**Treat skills like third-party dependencies:**

1. **Read the source before installing.** Skills are markdown and YAML files. If you cannot read the full skill in a few minutes, that is a red flag.

2. **Check the repository.** Look at stars, contributors, and commit history. A single-commit repository from an unknown account deserves scrutiny.

3. **Scan installed skills:**
   ```bash
   uvx mcp-scan@latest --skills
   ```
   This scans for known malicious patterns, prompt injection, and credential exposure.

4. **Be cautious of skills fetching external content at runtime.** The skill's behavior can change after you install it.

5. **Use the skill-security-auditor** (from alirezarezvani/claude-skills):
   ```bash
   python3 engineering/skill-security-auditor/scripts/skill_security_auditor.py /path/to/skill/
   ```
   Scans for command injection, code execution, data exfiltration, prompt injection, dependency supply chain risks, privilege escalation. Returns PASS / WARN / FAIL with remediation.

6. **Stick to known repositories.** Every skill in this document comes from a repository with visible maintainers and community activity.

**For enterprise deployment:**
- Establish a formal vetting and approval process for skills before team distribution
- Use version control and internal repositories for team skill distribution
- Periodically audit installed skills
- Organization admins can deploy skills workspace-wide via the admin console

---

## Reference: Complete SKILL.md Template

```yaml
---
name: your-skill-name
description: What it does. Use when user says "[trigger phrase 1]", "[trigger phrase 2]",
  or "[trigger phrase 3]". Verified on [environment]. Does not trigger for [exclusions].
license: MIT
metadata:
  author: Your Name
  version: 1.0.0
  category: your-category
---

## Your Skill Name

Brief one-paragraph description of what this skill does and why it exists.

## Step 1: [First Step]

Clear explanation of the first step.

If a script is needed:
```bash
python scripts/process.py --input $ARGUMENTS
```
Expected output: [describe success]

## Step 2: [Second Step]

Before executing this step, consult `references/api-patterns.md` for rate limiting
guidance and pagination patterns. Only load it if needed for this task.

## Examples

**Example 1: [most common scenario]**
User says: "..."
What happens: ...
Result: ...

## Troubleshooting

**Error: [specific error message]**
- Cause: [why it happens]
- Solution: [exact fix]

## Rules and Learnings

Rules updated from session feedback. Always read before executing.
```

**Reference: Repository Structure for Team Knowledge Registry**

```
your-org/research-skills/
├── .github/
│   └── workflows/
│       ├── validate.yml          # Validates plugin structure on PRs
│       └── marketplace.yml       # Regenerates marketplace.json on merge
├── plugins/
│   ├── training/
│   │   └── experiment-name/
│   │       ├── .claude-plugin/
│   │       │   └── plugin.json
│   │       ├── skills/experiment-name/
│   │       │   └── SKILL.md
│   │       ├── references/
│   │       │   ├── experiment-log.md
│   │       │   └── troubleshooting.md
│   │       └── scripts/
│   └── evaluation/
├── templates/
│   └── experiment-skill-template/
├── scripts/
│   ├── validate_plugins.py
│   └── generate_marketplace.py
├── marketplace.json
└── CLAUDE.md
```

**Reference: GitHub Actions Plugin Validation**

```yaml
# .github/workflows/validate.yml
name: Validate Plugins

on:
  pull_request:
    paths: ['plugins/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check plugin structure
        run: |
          for dir in plugins/*/*; do
            if [ -d "$dir/.claude-plugin" ]; then
              # Check plugin.json has required fields
              jq -e '.name and .description and .skills' \
                "$dir/.claude-plugin/plugin.json" > /dev/null || \
                { echo "Invalid plugin.json in $dir"; exit 1; }

              # Check SKILL.md exists
              find "$dir/skills" -name "SKILL.md" | grep -q . || \
                { echo "Missing SKILL.md in $dir"; exit 1; }

              echo "OK: $dir"
            fi
          done
```

**Reference: Quick Pre-Upload Checklist**

Before publishing or sharing any skill:

- [ ] Folder named in kebab-case
- [ ] `SKILL.md` file exists (exact spelling, case-sensitive)
- [ ] YAML frontmatter has `---` delimiters on both sides
- [ ] `name` field: kebab-case, no spaces, no capitals
- [ ] `description` includes WHAT the skill does AND WHEN to trigger it
- [ ] `description` includes specific trigger phrases users will say
- [ ] No XML angle brackets (`<` or `>`) anywhere in frontmatter
- [ ] `SKILL.md` body is under 500 lines
- [ ] Detailed documentation is in `references/` folders, not inline
- [ ] Instructions are specific and actionable
- [ ] Error handling and troubleshooting section included
- [ ] Tested triggering on obvious tasks
- [ ] Tested triggering on paraphrased requests
- [ ] Verified skill does NOT trigger on unrelated topics
- [ ] Source reviewed for security before installation (for community skills)
