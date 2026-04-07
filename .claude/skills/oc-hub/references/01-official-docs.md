# Claude Code Official Documentation

A comprehensive reference for Claude Code — the agentic coding CLI, IDE extension, web, desktop, and mobile surfaces built on Anthropic's Claude models.

---

## Table of Contents

1. [Overview and Installation](#1-overview-and-installation)
2. [Quickstart](#2-quickstart)
3. [How Claude Code Works](#3-how-claude-code-works)
4. [Memory and CLAUDE.md](#4-memory-and-claudemd)
5. [Common Workflows](#5-common-workflows)
6. [Best Practices](#6-best-practices)
7. [Skills](#7-skills)
8. [Custom Subagents](#8-custom-subagents)
9. [Hooks](#9-hooks)
10. [Plugins](#10-plugins)
11. [Remote Control](#11-remote-control)
12. [VS Code Extension](#12-vs-code-extension)
13. [Claude Code on the Web](#13-claude-code-on-the-web)
14. [Chrome Integration](#14-chrome-integration)
15. [Monitoring and OpenTelemetry](#15-monitoring-and-opentelemetry)
16. [Server-Side Compaction API](#16-server-side-compaction-api)
17. [Agent Skills API](#17-agent-skills-api)
18. [Platform Release Notes](#18-platform-release-notes)

---

## 1. Overview and Installation

Claude Code is an agentic coding tool that lives in your terminal, IDE, and browser. It understands your entire codebase, writes and edits files, runs commands, browses the web, and orchestrates multi-agent workflows — all while keeping humans in the loop with fine-grained permission controls.

### Surfaces

| Surface | Description |
|---|---|
| CLI (`claude`) | Interactive REPL and headless automation in your terminal |
| VS Code / JetBrains extension | Graphical panel embedded in your IDE |
| Claude Code on the web (`claude.ai/code`) | Cloud-hosted sessions in Anthropic-managed VMs |
| Remote Control | Control a local session from any browser or mobile device |
| Claude mobile app | Continue sessions started on your machine |

### Installation

**One-line installer (recommended):**

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**npm (manual):**

```bash
npm install -g @anthropic-ai/claude-code
```

**Homebrew (macOS):**

```bash
brew install claude-code
```

**WinGet (Windows):**

```bash
winget install Anthropic.ClaudeCode
```

The native installer enables automatic updates. After installing, run `claude` to start your first session.

### Requirements

- Node.js 18+
- macOS, Linux, or Windows (WSL recommended for Windows)
- A claude.ai account (Pro, Max, Team, or Enterprise) **or** an Anthropic API key
- Git (optional but recommended)

### Authentication

```bash
claude        # prompts for login on first run
/login        # switch accounts or reauthenticate
/logout       # sign out
```

Set `ANTHROPIC_API_KEY` in your environment to authenticate via API key instead of OAuth.

### What Claude Code Can Do

- Explore, understand, and navigate large codebases
- Write, edit, and refactor code across multiple files
- Run tests, build commands, linters, and arbitrary shell commands
- Search the web and read URLs
- Create and review pull requests
- Coordinate parallel workstreams via subagents
- Connect to external services via MCP servers
- Operate headlessly for CI/CD automation

---

## 2. Quickstart

### First Session

```bash
cd /path/to/your/project
claude
```

Claude Code reads your project files, git history, and any `CLAUDE.md` instructions to orient itself.

### Essential Commands

| Command | What it does |
|---|---|
| `claude` | Start interactive session in current directory |
| `claude "fix the login bug"` | Start session with an initial prompt |
| `claude -c` / `--continue` | Resume the most recent session |
| `claude -r` / `--resume` | Pick a session to resume from a list |
| `claude -n` / `--name "title"` | Start session with a custom name |
| `claude --permission-mode plan` | Start in read-only plan mode |
| `claude --headless "task"` | Run a task non-interactively and exit |
| `/help` | Show all slash commands |
| `/compact` | Summarize context to free up tokens |
| `/status` | Show current account and subscription |
| `/clear` | Clear conversation history |
| `Ctrl+C` | Cancel the current operation |
| `Esc` | Interrupt Claude mid-response |
| `Esc Esc` | Rewind to before the last message |

### 8-Step First Workflow

1. Start Claude: `claude`
2. Ask Claude to describe the codebase: `"Give me an overview of this project"`
3. Ask about a specific area: `"How does authentication work?"`
4. Make a small change: `"Add input validation to the signup form"`
5. Review changes: Claude will show diffs before writing
6. Run tests: `"Run the test suite and fix any failures"`
7. Create a commit: `"Commit these changes with an appropriate message"`
8. End session: `Ctrl+D` or `/exit`

### Pro Tips

- **Be specific**: "Add error handling to the `fetchUser` function in `api/users.js`" works better than "add error handling"
- **Iterate**: Start broad, then narrow down — Claude tracks context across turns
- **Use `@` references**: Type `@filename` to include a specific file in context
- **Check permissions**: Claude asks before running destructive commands; review carefully
- **Create CLAUDE.md**: Add project-specific instructions to guide every session (see [Memory and CLAUDE.md](#4-memory-and-claudemd))

---

## 3. How Claude Code Works

### The Agentic Loop

Claude Code operates in a loop:

1. **Gather context** — read files, search code, run commands to understand the situation
2. **Take action** — write/edit files, execute commands, call tools
3. **Verify results** — check outputs, run tests, confirm correctness
4. Repeat until the task is complete

Each step uses one or more built-in tools. Claude decides which tools to call based on your prompt and the current state of the codebase.

### Built-in Tools

| Category | Tools |
|---|---|
| File operations | Read, Write, Edit, MultiEdit, Glob, LS |
| Search | Grep, Task (semantic search) |
| Execution | Bash, computer-use shell |
| Web | WebFetch, WebSearch |
| Code intelligence | mcp__ide__getDiagnostics, mcp__ide__executeCode (VS Code) |
| Agent coordination | Task (spawn subagent), MessageAgent |

### Execution Environments

| Environment | Used for |
|---|---|
| Local shell (Bash) | Commands, scripts, test runners, build tools |
| MCP servers | External APIs, databases, proprietary services |
| Subagents | Isolated parallel workstreams |
| Cloud VMs | Claude Code on the web sessions |

### Context Window Management

Claude Code works within a finite context window. Strategies to manage it:

- **`/compact`**: Summarizes the conversation in place; preserves key decisions and code snippets
- **`Compact Instructions`** in `CLAUDE.md`: Custom summary prompt for `/compact`
- **Subagents**: Each subagent has its own isolated context, preventing pollution of the main session
- **Skills on-demand**: Skill instructions are only loaded when the skill is invoked

When context approaches the limit, Claude Code automatically compacts. You can also compact manually at any point.

### Session and Branch Management

- **`--continue` / `-c`**: Resume the most recent session
- **`--resume` / `-r`**: Interactive session picker with keyboard navigation
- **`--fork-session`**: Branch a new session from the current point
- **`-n` / `/rename`**: Set a session title
- Sessions are persisted locally and listed in the session picker

### Git Worktrees for Parallel Sessions

```bash
claude --worktree      # -w shorthand
claude -w "feature-A"
```

Each worktree session gets its own git branch and working directory, preventing conflicts when running multiple Claude Code sessions on the same repo simultaneously.

### Checkpoints

Before every file edit, Claude Code saves a checkpoint. To restore:

- **`Esc Esc`**: Rewind to before the last message (restores all files changed in that turn)
- **`/rewind`**: Interactive checkpoint browser

Checkpoints are stored per-file and are available for the duration of the session.

### Permission Modes

| Mode | Behavior |
|---|---|
| Default | Asks for confirmation before any file write or shell command |
| Auto-accept edits | Automatically accepts file edits; still asks for shell commands |
| Plan mode | Read-only; no writes or commands; use `Shift+Tab` to toggle or `claude --permission-mode plan` |
| `bypassPermissions` | Skips all permission prompts (for automated pipelines; use with caution) |

Toggle between modes with `Shift+Tab` during a session. Permission mode shows in the status bar.

**Settings-based allowlists** in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": ["Bash(npm run *)", "Edit(src/**)"],
    "deny": ["Bash(rm -rf *)"]
  }
}
```

### Extended Thinking

Claude 4 models (Opus 4.6, Sonnet 4.6) use adaptive reasoning by default. To explicitly request deep thinking:

- Type `think`, `think hard`, `think harder`, or `ultrathink` in your prompt
- Use `/effort high` (or `medium`/`low`) to set effort level for the session
- Set `MAX_THINKING_TOKENS` environment variable to control budget
- Disable with `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1`

### Working Effectively

- Break large tasks into steps — give Claude one clear objective at a time
- Ask Claude to explain its plan before executing
- Use Plan mode (`--permission-mode plan`) for exploratory or risky tasks
- Review diffs carefully before accepting
- Use `/compact` proactively before context fills up
- Keep `CLAUDE.md` updated with project conventions Claude should follow

---

## 4. Memory and CLAUDE.md

### Two Memory Systems

| System | Written by | Loaded when | Purpose |
|---|---|---|---|
| `CLAUDE.md` | You (human) | Every session start | Project instructions, conventions, constraints |
| Auto memory (`MEMORY.md`) | Claude | Every session start (first 200 lines) | Claude's notes about decisions, progress, context |

### CLAUDE.md

#### Location and Scope

| File path | Scope |
|---|---|
| `CLAUDE.md` (project root) | All sessions in this project |
| `.claude/CLAUDE.md` | Same scope, alternative location |
| `~/.claude/CLAUDE.md` | All sessions on this machine (global) |
| Any subdirectory `CLAUDE.md` | Sessions in that directory and below |

Claude reads all applicable CLAUDE.md files at session start, from global down to the current directory.

#### What to Include

- Build and test commands
- Code style preferences (naming conventions, import order, etc.)
- Architecture decisions and constraints
- File/directory structure overview
- Workflows specific to this project (how to deploy, how to run migrations, etc.)
- Things Claude should never do (e.g., "never edit generated files in `dist/`")

#### What to Exclude

- Sensitive credentials or secrets
- Very long documentation that rarely applies
- Instructions that change frequently (use auto memory for that)

#### Imports

Reference other files from CLAUDE.md using `@path` syntax:

```markdown
@./docs/architecture.md
@./src/api/README.md
```

The contents of the referenced file are inlined at that position. Paths are relative to the CLAUDE.md file.

#### Path-Scoped Rules

Create rules that only apply to specific directories by placing CLAUDE.md files in those directories, or by using `.claude/rules/`:

```
.claude/rules/frontend.md       # applies to all files matching the rule's paths
.claude/rules/database.md
```

Each rules file uses YAML frontmatter to specify the paths it governs:

```markdown
---
paths:
  - "src/frontend/**"
  - "*.tsx"
---

# Frontend Rules

Always use Tailwind classes, never inline styles.
```

#### Excluding Files from CLAUDE.md Loading

```json
// .claude/settings.json
{
  "claudeMdExcludes": ["**/node_modules/**", "**/vendor/**"]
}
```

#### Compact Instructions

Add a `Compact Instructions` section to CLAUDE.md to customize the summary Claude generates when `/compact` runs:

```markdown
## Compact Instructions

When compacting, always preserve:
- The current task and any incomplete steps
- File paths of recently edited files
- Test failures and their error messages
- Any decisions about which approach to use
```

### Auto Memory (MEMORY.md)

Claude writes its own notes to `~/.claude/projects/<project-hash>/memory/MEMORY.md`. The first 200 lines are loaded at every session start.

Use the `/memory` command to open and review Claude's memory file. You can edit it manually to correct or remove notes.

Auto memory is distinct from CLAUDE.md: CLAUDE.md is your instructions to Claude; MEMORY.md is Claude's scratch pad for its own continuity.

---

## 5. Common Workflows

### Explore a Codebase

```
"Give me a high-level overview of this codebase"
"How does the authentication system work?"
"What does the /api/users endpoint do?"
"Find all places where we handle payment failures"
```

Use `@filename` to include specific files in context:

```
"Explain @src/auth/middleware.js and how it relates to @src/routes/index.js"
```

### Fix a Bug

1. Describe the symptom: `"The login form throws a 500 error when the email contains a plus sign"`
2. Let Claude reproduce: `"Run the failing test: npm test auth"`
3. Review the fix before accepting
4. Verify: `"Run the tests again and confirm they pass"`

### Refactor Code

For large refactors, use Plan mode first:

```bash
claude --permission-mode plan
```

Then:
1. `"Plan a refactor of the payment module to use the new Stripe SDK"`
2. Review the plan (Claude cannot write files in plan mode)
3. Switch to normal mode and execute step by step

For cross-file refactors, consider spawning subagents for different parts of the codebase to avoid context overflow.

### Run Tests

```
"Run the full test suite"
"Run only the tests in src/auth/ and fix any failures"
"Add tests for the edge cases in the validateEmail function"
```

### Create a Pull Request

```
"Create a PR for these changes with a descriptive title and body"
"Review my staged changes and suggest a commit message"
"Squash my last 3 commits and push to origin"
```

### Document Code

```
"Add JSDoc comments to all exported functions in src/api/"
"Write a README for this module explaining its purpose and usage"
"Update the CHANGELOG with the changes from this PR"
```

### Use Images

Paste images directly into the Claude Code prompt or use `@` to reference image files:

```
@screenshots/error.png
"What's causing this error?"
```

### Configure Extended Thinking

| Setting | How to configure |
|---|---|
| Trigger deep thinking | Add `think`, `think hard`, or `ultrathink` to prompt |
| Set effort level | `/effort high` / `/effort medium` / `/effort low` |
| Token budget | `MAX_THINKING_TOKENS=10000` env var |
| Disable adaptive thinking | `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING=1` |

### Session Management

```bash
claude -c                    # continue last session
claude -r                    # pick session to resume
claude -n "My Feature"       # start named session
/rename "New Name"           # rename current session
/fork                        # fork current session
```

In the session picker: arrow keys to navigate, Enter to resume, `d` to delete.

### Git Worktrees for Parallel Work

```bash
# Start two parallel sessions on different branches
claude -w "feature/auth-redesign"
claude -w "bugfix/payment-timeout"
```

Each session operates in its own worktree with no shared working tree state.

### Notifications

Claude Code sends desktop notifications when long-running tasks complete. On macOS, notifications use the system notification center. On Linux, `notify-send` must be available.

To trigger a sound on task completion, add a PostToolUse hook that runs a sound command.

### Unix-Style Usage

Claude Code integrates with standard Unix pipelines:

```bash
# Pipe content to Claude
cat error.log | claude "what's causing these errors?"

# Use Claude in a pipeline
claude --headless "summarize the changes in this diff" < git.diff

# Capture Claude's output
claude --headless "list all API endpoints" --output-format json > endpoints.json
```

**Output formats** (`--output-format` flag):

| Format | Description |
|---|---|
| `text` (default) | Plain text response |
| `json` | Structured JSON with message and metadata |
| `stream-json` | Newline-delimited JSON stream |

### Using MCP Servers

```
/mcp                         # list connected MCP servers and their costs
```

MCP tools appear as `mcp__<server>__<tool>` in tool calls. Context cost per server is shown in `/mcp`.

---

## 6. Best Practices

### Context Is the Primary Constraint

The context window is finite and expensive. Manage it actively:

- Use `/compact` before it fills up, not after
- Write `Compact Instructions` in CLAUDE.md to preserve what matters
- Use subagents to isolate large tasks in their own contexts
- Load skills on-demand rather than pasting large instructions
- Avoid including entire files when only a function is needed — use `@` references and let Claude narrow scope

### Verification Strategies

Don't trust, verify:

- Ask Claude to run tests after every substantive change
- Use Plan mode to review intent before execution
- For risky operations, use `--permission-mode plan` and manually review the plan
- Enable hooks to log or block specific tool calls

### Explore-Plan-Code Workflow

For complex tasks:

1. **Explore**: `"Read the codebase and understand how X works"` (no changes)
2. **Plan**: `"Write a detailed plan for implementing Y"` (plan mode or just prose)
3. **Code**: Execute the plan step by step, verifying as you go

This prevents Claude from diving into implementation before fully understanding the problem.

### Prompt Specificity

| Vague | Specific |
|---|---|
| "Fix the bug" | "Fix the TypeError in `api/users.js:47` where `user.profile` can be undefined" |
| "Add tests" | "Add unit tests for `validateEmail` in `src/utils/validation.js` covering empty string, invalid format, and plus signs in the local part" |
| "Refactor this" | "Refactor the `PaymentService` class to use dependency injection, keeping the same public API" |

### CLAUDE.md Best Practices

**Include:**
- `npm run dev` / `npm test` / `npm run build` commands
- Code style rules (ESLint config summary, naming conventions)
- Branch and commit message conventions
- File structure overview
- "Never edit X files"

**Exclude:**
- API keys, passwords, tokens
- Very long design documents
- Information that's already obvious from the codebase

Keep CLAUDE.md under 500 lines. Use `@imports` to reference longer documents.

### Permissions Configuration

Store project-level permissions in `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(git *)",
      "Edit(src/**)",
      "Edit(tests/**)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(curl * | bash)"
    ]
  }
}
```

Store personal/machine-level permissions in `~/.claude/settings.json`.

### Hooks for Automated Guardrails

Use hooks to enforce rules that Claude should always follow without relying on prompt instructions (see [Hooks](#9-hooks)):

- Block writes to generated/vendor files
- Auto-run linter after every file edit
- Log all tool calls for audit
- Require test runs before commits

### Subagents for Large Tasks

When a task spans many files or many steps:

- Create a subagent for each independent concern
- Let the main Claude orchestrate
- Each subagent has its own context, preventing overflow
- Use `isolation: worktree` for subagents that need filesystem isolation

### Session Hygiene

- Name sessions with `/rename` or `-n` for easy retrieval
- Fork sessions before risky experiments
- Compact frequently
- Archive or delete old sessions from the session picker

### Automation and CI/CD

```bash
# Headless mode for scripts
claude --headless --permission-mode bypassPermissions "run linter and fix all errors"

# In GitHub Actions
- name: Claude Code review
  run: claude --headless "review this PR for security issues" --output-format json
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

Use `bypassPermissions` only in sandboxed CI environments where the codebase and commands are trusted.

### Common Failure Patterns to Avoid

- **Context overflow mid-task**: Compact before starting large tasks, not after getting stuck
- **Vague instructions**: Always specify file paths, function names, and expected behavior
- **Skipping verification**: Always run tests; never assume edits are correct
- **Over-trusting auto-approve**: Review the allow list in settings.json carefully
- **Missing CLAUDE.md**: Without project instructions, Claude makes guesses about conventions

---

## 7. Skills

Skills are reusable instructions packaged as markdown files. They can be invoked with a slash command, run automatically, or loaded on demand by subagents.

### Bundled Skills

| Skill | Invocation | Description |
|---|---|---|
| Batch | `/batch` | Apply the same prompt to multiple files in parallel |
| Claude API | `/claude-api` | Build apps using the Anthropic SDK |
| Debug | `/debug` | Systematic debugging workflow |
| Loop | `/loop` | Repeat a command on an interval |
| Simplify | `/simplify` | Review changed code for quality and reduce complexity |

### Creating a Skill

Create a skill directory and a `SKILL.md` file:

```
.claude/skills/my-skill/
  SKILL.md
  helper-script.sh       # optional supporting files
  prompt-template.txt    # optional supporting files
```

**SKILL.md frontmatter:**

```yaml
---
name: my-skill
description: "One-line description shown in the skill picker"
user-invocable: true           # show as /my-skill slash command (default: true)
disable-model-invocation: false # run the instructions without model (default: false)
context: fork                  # run in forked context (default: share parent)
allowed-tools:                 # restrict tools available in this skill
  - Read
  - Bash(npm test *)
---

# My Skill Instructions

Everything below the frontmatter is the skill prompt/instructions.
```

### Frontmatter Reference

| Field | Type | Default | Description |
|---|---|---|---|
| `name` | string | directory name | Skill identifier and slash command name |
| `description` | string | — | Shown in skill picker and to the model |
| `user-invocable` | bool | `true` | Whether the skill appears as a slash command |
| `disable-model-invocation` | bool | `false` | Run instructions as a shell script, no model call |
| `context` | `fork` \| (empty) | share parent | `fork` gives the skill its own isolated context |
| `allowed-tools` | list | all parent tools | Restrict tools this skill can use |

### Argument Substitution

Skills can accept arguments:

```markdown
---
name: test-file
description: "Run tests for a specific file"
---

Run tests for $ARGUMENTS and fix any failures.
```

Invoke with: `/test-file src/auth/login.js`

Multiple positional args: use `$1`, `$2`, `$3`, etc.

**Built-in variables:**

| Variable | Value |
|---|---|
| `$ARGUMENTS` | Everything after the skill name |
| `$1`, `$2`, ... | Positional arguments |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Absolute path to the skill directory |

### Dynamic Content Injection

Use `!` before a shell command to inject its output into the skill prompt at invocation time:

```markdown
---
name: project-status
description: "Report current project status"
---

Current git status:
!git status --short

Current failing tests:
!npm test 2>&1 | tail -20

Report on the above and suggest next steps.
```

### `disable-model-invocation`

When set to `true`, the skill's SKILL.md body is executed as a shell script directly, without a model call. Useful for skills that are just shell automation:

```yaml
---
name: reset-db
disable-model-invocation: true
---
#!/bin/bash
npm run db:reset
npm run db:seed
echo "Database reset complete"
```

### Plugin Namespaced Skills

Skills from plugins are invoked with `plugin-name:skill-name`:

```
/my-plugin:code-review
```

### Troubleshooting Skills

- Skill not appearing: check `user-invocable: true` and that the file is at `.claude/skills/<name>/SKILL.md`
- Args not substituting: use `$ARGUMENTS` (uppercase, no curly braces for the full string)
- Tool access errors: add required tools to `allowed-tools` or remove the restriction

---

## 8. Custom Subagents

Subagents are isolated Claude instances that run subtasks in their own context windows. They can be spawned automatically (via delegation) or explicitly (via `@mention`).

### Built-in Subagents

| Name | Role |
|---|---|
| `explore` | Context gathering, codebase exploration |
| `plan` | Planning, architecture, spec writing |
| General purpose | Code execution, edits, general tasks |

### Creating a Subagent

Create a file in `.claude/agents/`:

```
.claude/agents/code-reviewer.md
.claude/agents/data-scientist.md
```

**Agent file structure:**

```markdown
---
name: code-reviewer
description: "Reviews code for security, style, and correctness. Invoked for PR reviews and code review requests."
model: claude-opus-4-6
tools:
  - Read
  - Grep
  - Bash(git diff *)
disallowedTools:
  - Write
  - Edit
permissionMode: default
maxTurns: 20
skills:
  - simplify
---

You are a code reviewer. Focus on:
1. Security vulnerabilities
2. Logic errors
3. Code style consistency with the project

Always provide specific, actionable feedback with file and line references.
```

### Frontmatter Reference

| Field | Type | Description |
|---|---|---|
| `name` | string | Identifier; used for `@name` invocation |
| `description` | string | Describes when to use this agent; used for automatic delegation matching |
| `model` | string | Model alias: `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5`, etc. |
| `tools` | list | Allowlist of tools this agent can use |
| `disallowedTools` | list | Denylist of tools (use one or the other, not both) |
| `permissionMode` | string | `default`, `acceptEdits`, `plan`, `bypassPermissions` |
| `maxTurns` | int | Maximum agentic loop iterations |
| `skills` | list | Skills pre-loaded for this agent |
| `mcpServers` | list | MCP servers available to this agent |
| `hooks` | object | Agent-specific hooks (same format as session hooks) |
| `memory` | list | Memory scopes: `session`, `project`, `global`, `agent` |
| `background` | bool | Run without interrupting main session (default: `false`) |
| `effort` | string | `low`, `medium`, `high` — maps to thinking budget |
| `isolation` | string | `none` (default), `worktree` — give agent its own git worktree |

### Agent Scope and Priority

| Location | Scope |
|---|---|
| `.claude/agents/` (project) | Available in this project |
| `~/.claude/agents/` (global) | Available in all projects |
| Plugin-provided agents | Available when plugin is installed |

Project-level agents override global agents with the same name.

### Invoking Subagents

**Automatic delegation:** Claude delegates to a subagent when your request matches the agent's `description`. Make descriptions specific and action-oriented.

**Explicit invocation via `@mention`:**

```
@code-reviewer please review the changes in src/auth/
@data-scientist analyze the CSV in data/sales-q4.csv and produce a summary
```

**From Claude's perspective** — you can also ask Claude to use a specific agent:

```
"Use the db-reader agent to query the production analytics database"
```

### Background vs Foreground Agents

- **Foreground** (default): The main session pauses while the subagent runs; results stream back
- **Background** (`background: true`): The subagent runs concurrently; the main session continues

Background agents are useful for long-running tasks (test runs, builds) while you continue other work.

### Agent Memory

The `memory` field controls which memory stores the agent reads from and writes to:

| Scope | Storage location |
|---|---|
| `session` | In-memory only; lost when session ends |
| `project` | `~/.claude/projects/<project>/memory/MEMORY.md` |
| `global` | `~/.claude/memory/MEMORY.md` |
| `agent` | `~/.claude/agents/<name>/memory/MEMORY.md` |

### Parallel Research Pattern

Spawn multiple background agents simultaneously:

```
"Simultaneously: have @explore summarize the auth module, @explore summarize the payment module, and @explore summarize the notification module. Then synthesize their findings."
```

Each runs in parallel; the main session waits for all to complete before synthesizing.

### Resume Pattern

For long multi-session tasks, a subagent can read a MEMORY.md to resume where it left off:

```markdown
---
name: migrator
memory:
  - agent
---

Read your agent memory to find where the migration left off, then continue.
```

### Auto-Compaction

Subagents compact automatically when their context window fills. The compaction uses the parent session's `Compact Instructions` if no agent-specific ones are provided.

### Example: DB Reader with Validation

```markdown
---
name: db-reader
description: "Reads from the analytics database. Use for data queries, reporting, and analysis."
tools:
  - Bash(psql -h analytics-db -U readonly *)
disallowedTools:
  - Write
  - Edit
permissionMode: plan
---

You have read-only access to the analytics database. You may run SELECT queries only.
Never run INSERT, UPDATE, DELETE, DROP, or any DDL statements.

Before running any query, explain what it does and what you expect it to return.
```

### Managing Agents

```
/agents          # list all available subagents
```

---

## 9. Hooks

Hooks execute shell commands, HTTP requests, prompts, or subagents in response to lifecycle events in the Claude Code session. They run outside the agentic loop and are not part of the model's context.

### Hook Events

| Event | Fires when |
|---|---|
| `SessionStart` | Session begins |
| `PreToolUse` | Before any tool call |
| `PostToolUse` | After any tool call completes |
| `Stop` | Claude finishes responding (not interrupted) |
| `Notification` | Claude sends a status notification |
| `PermissionRequest` | A tool needs permission to proceed |
| `SubagentStart` | A subagent begins |
| `SubagentStop` | A subagent finishes |

### Hook Types

| Type | Description |
|---|---|
| `command` | Run a shell command |
| `http` | Make an HTTP request (POST by default) |
| `prompt` | Inject text into the conversation as a user message |
| `agent` | Spawn a subagent |

### Hook Configuration

Hooks are defined in `.claude/settings.json` (project) or `~/.claude/settings.json` (global):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": { "tool_name": "Edit" },
        "type": "command",
        "command": "npm run lint -- $CLAUDE_FILE_PATHS 2>&1"
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "afplay /System/Library/Sounds/Glass.aiff"
      }
    ]
  }
}
```

### Matchers

Matchers filter which tool calls trigger a hook. Available matchers by event:

| Event | Matcher fields |
|---|---|
| `PreToolUse` / `PostToolUse` | `tool_name`, `tool_input` |
| `PermissionRequest` | `tool_name`, `permission_type` |
| `SubagentStart` / `SubagentStop` | `agent_name` |

Matcher values support glob patterns:

```json
{ "matcher": { "tool_name": "Bash", "tool_input": { "command": "rm *" } } }
{ "matcher": { "tool_name": "Edit", "tool_input": { "file_path": "src/**" } } }
```

### Hook Location and Scope

| File | Scope |
|---|---|
| `~/.claude/settings.json` | All sessions (global) |
| `.claude/settings.json` | This project only |
| `.claude/settings.local.json` | This project, not committed to git |
| Subagent frontmatter `hooks:` | This subagent only |

### stdin/stdout Communication

Hooks receive context via stdin as JSON and communicate back via stdout:

**stdin payload (PreToolUse example):**
```json
{
  "event": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "rm -rf /tmp/build" },
  "session_id": "abc123"
}
```

**stdout to control behavior (exit codes and JSON):**

| Exit code | Meaning |
|---|---|
| `0` | Allow the tool call to proceed |
| `2` | Block the tool call; Claude sees the stdout as an error message |

For blocking with a message:

```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

if echo "$COMMAND" | grep -q "rm -rf"; then
  echo "Blocked: rm -rf patterns are not allowed"
  exit 2
fi
exit 0
```

### Structured JSON Output

For `prompt` type hooks and rich feedback, output JSON:

```json
{
  "message": "Lint failed: 3 errors found",
  "type": "error",
  "details": "src/auth.js:14: 'token' is defined but never used"
}
```

### Example: Protect Critical Files

```bash
#!/bin/bash
# .claude/hooks/protect-files.sh
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

PROTECTED=("package-lock.json" "yarn.lock" ".env" "*.pem")

for pattern in "${PROTECTED[@]}"; do
  if [[ "$FILE" == $pattern ]]; then
    echo "Blocked: $FILE is a protected file"
    exit 2
  fi
done
exit 0
```

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": { "tool_name": "Edit" },
        "type": "command",
        "command": "bash .claude/hooks/protect-files.sh"
      }
    ]
  }
}
```

### Example: Auto-Approve Specific Permissions

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": { "tool_name": "Bash", "tool_input": { "command": "npm run *" } },
        "type": "command",
        "command": "echo '{\"approved\": true}'"
      }
    ]
  }
}
```

### Environment Variables in Hooks

| Variable | Value |
|---|---|
| `$CLAUDE_FILE_PATHS` | Space-separated list of files involved in the current tool call |
| `$CLAUDE_SESSION_ID` | Current session ID |
| `$CLAUDE_TOOL_NAME` | Tool name that triggered the hook |

### Troubleshooting Hooks

- **Hook not firing**: Check that the event name and matcher fields exactly match the Claude Code event/tool names
- **Exit code ignored**: Only `PreToolUse` and `PermissionRequest` hooks can block; `PostToolUse` exit codes do not block
- **JSON parse errors**: Validate your hook's JSON output with `echo '...' | jq .`
- **Command not found**: Use absolute paths in `command` fields; hooks may not have `PATH` set correctly

---

## 10. Plugins

Plugins bundle skills, hooks, subagents, and MCP servers into a shareable package that can be installed into any project or globally.

### Plugin Structure

```
.claude/plugins/my-plugin/
  plugin.json           # manifest
  skills/
    code-review/
      SKILL.md
  agents/
    reviewer.md
  hooks/
    post-edit.sh
  mcp/
    server-config.json
```

### plugin.json

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Code review automation",
  "skills": ["skills/code-review"],
  "agents": ["agents/reviewer.md"],
  "hooks": { "PostToolUse": [{ "type": "command", "command": "hooks/post-edit.sh" }] }
}
```

### Installing Plugins

```bash
# From a directory
claude plugin install ./path/to/plugin

# Scope: project (default) or global
claude plugin install ./plugin --scope global
```

### Plugin Marketplaces

Plugins can be distributed through:
- Claude Code plugin marketplaces (browse via VS Code extension's plugin manager)
- Git repositories (install from URL)
- Local directories

### Using Plugin Skills

Skills from plugins are namespaced:

```
/my-plugin:code-review
/my-plugin:simplify
```

---

## 11. Remote Control

Remote Control lets you continue a local Claude Code session from any device — a phone, tablet, or another browser — without moving anything to the cloud.

### Requirements

- Subscription: Pro, Max, Team, or Enterprise (API keys not supported)
- Authentication: sign in via `claude` → `/login` using claude.ai OAuth
- On Team/Enterprise: an admin must enable Remote Control in admin settings

### Starting a Remote Control Session

**Server mode** (dedicated Remote Control process):

```bash
claude remote-control
claude remote-control --name "My Project"
```

The process stays running in your terminal, waiting for connections. Press spacebar to toggle QR code display.

**Interactive mode** (full terminal session + remote access):

```bash
claude --remote-control
claude --remote-control "My Project"
```

You can type locally and remotely simultaneously; the conversation stays in sync.

**From inside an existing session:**

```
/remote-control
/remote-control My Project
```

Carries over existing conversation history.

### `claude remote-control` Flags

| Flag | Description |
|---|---|
| `--name "title"` | Set session title visible in the session list |
| `--spawn same-dir` | Concurrent sessions share the working directory (default) |
| `--spawn worktree` | Each concurrent session gets its own git worktree |
| `--capacity N` | Maximum concurrent sessions (default: 32) |
| `--verbose` | Show detailed connection and session logs |
| `--sandbox` / `--no-sandbox` | Enable/disable filesystem and network sandboxing |

Press `w` at runtime to toggle between `same-dir` and `worktree` spawn modes.

### Connecting from Another Device

Three methods:

1. **Direct URL**: Open the session URL displayed in the terminal
2. **QR code**: Scan with phone to open in the Claude app
3. **Session list**: Open `claude.ai/code` or the Claude app; find session by name (shows computer icon with green dot when online)

To get the Claude app QR code:

```
/mobile
```

### Enable Remote Control for All Sessions

```
/config
```

Set "Enable Remote Control for all sessions" to `true`. With this on, every interactive Claude Code process automatically registers a remote session.

### Security Model

- Claude Code makes **outbound HTTPS only** — no inbound ports are opened
- Traffic routes through the Anthropic API over TLS
- Credentials are short-lived and scoped to a single purpose
- The session runs entirely on your machine; the browser/phone is just a UI

### Limitations

- One remote session per interactive process (use server mode with `--spawn` for multiple)
- Terminal must stay open; closing it ends the session
- Network outage > ~10 minutes causes session timeout

### Remote Control vs Claude Code on the Web

| | Remote Control | Claude Code on the web |
|---|---|---|
| Runs on | Your machine | Anthropic cloud VMs |
| Local tools/MCP | Yes | No |
| Filesystem access | Your local filesystem | Cloud VM filesystem |
| When to use | Continuing local work on another device | Starting fresh without local setup |

### Troubleshooting

**"Remote Control is not yet enabled for your account"**

Check for these env vars and unset them:
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` or `DISABLE_TELEMETRY`
- `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, or `CLAUDE_CODE_USE_FOUNDRY` (Remote Control requires claude.ai auth)

If none are set: run `/logout` then `/login`.

**"Remote Control is disabled by your organization's policy"**

Run `/status` to check your login method and subscription:
- If authenticated with API key: run `/login` and choose the claude.ai option; unset `ANTHROPIC_API_KEY`
- If Team/Enterprise: ask an admin to enable Remote Control at `claude.ai/admin-settings/claude-code`
- If admin toggle is grayed out: a data retention/compliance config blocks it; contact Anthropic support

**"Remote credentials fetch failed"**

Run with `--verbose` to see the full error:

```bash
claude remote-control --verbose
```

Common causes: not signed in, firewall blocking outbound port 443, or inactive subscription.

---

## 12. VS Code Extension

The Claude Code VS Code extension embeds Claude Code in a graphical panel inside VS Code and JetBrains IDEs.

### Prerequisites and Installation

- VS Code 1.90+ or compatible JetBrains IDE
- Claude Code CLI installed and authenticated
- Install from the VS Code Marketplace: search "Claude Code"

The extension icon (spark/lightning) appears in the Activity Bar.

### Prompt Box Features

- **Permission mode selector**: toggle between Default, Auto-accept, and Plan mode
- **Command menu** (`/`): access slash commands and skills
- **Context indicator**: shows current token usage
- **Thinking indicator**: shows when extended thinking is active
- **Multi-line input**: `Shift+Enter` for newline

### Adding File Context

- `@` in the prompt box opens a fuzzy file picker
- `Option+K` (macOS) / `Alt+K` (Windows/Linux) while a file is open inserts a reference to that file
- Drag files from the explorer into the prompt box
- Right-click a file in the explorer → "Add to Claude Code context"

### Conversation History

Conversations persist in the VS Code extension panel. Use the session picker (clock icon) to switch between or resume sessions.

### Plugin Management

The extension includes a plugin manager:
- Browse and install community plugins
- Scope plugins to workspace or user level
- Enable/disable individual plugins

### Chrome Integration

With the Chrome extension installed:

```
@browser    # reference the current browser tab in context
```

See [Chrome Integration](#14-chrome-integration) for full details.

### Commands and Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Option+K` / `Alt+K` | Insert reference to current file |
| `Shift+Tab` | Toggle permission mode (Default → Auto-accept → Plan) |
| `Shift+Enter` | New line in prompt box |
| `Cmd+K` / `Ctrl+K` | Open Claude Code panel |
| `Esc` | Cancel current operation |
| `Esc Esc` | Rewind to before last message |

### Extension Settings

| Setting | Description |
|---|---|
| `claudeCode.theme` | `system`, `light`, `dark` |
| `claudeCode.fontSize` | Panel font size |
| `claudeCode.autoStart` | Start Claude Code on VS Code launch |
| `claudeCode.defaultPermissionMode` | Starting permission mode |

### IDE MCP Server

The VS Code extension provides an IDE MCP server on `127.0.0.1` with two tools:

| Tool | Description |
|---|---|
| `mcp__ide__getDiagnostics` | Get lint/type errors from VS Code's language servers for a file |
| `mcp__ide__executeCode` | Execute code in VS Code's integrated terminal or notebook |

These tools allow Claude to see real-time errors from TypeScript, ESLint, Pylance, etc. without running a separate process.

### Rewind / Checkpoints in VS Code

The rewind button (↩ icon) in the conversation panel restores files to their pre-turn state. The VS Code extension shows which files were modified in each turn.

### CLI vs Extension Feature Comparison

| Feature | CLI | Extension |
|---|---|---|
| All slash commands | Yes | Yes |
| Hooks | Yes | Yes |
| Subagents | Yes | Yes |
| MCP servers | Yes | Yes |
| File drag-and-drop | No | Yes |
| IDE diagnostics | No | Yes (via IDE MCP) |
| Plugin manager GUI | No | Yes |
| `@browser` context | No | Yes (with Chrome ext) |

### Troubleshooting

- **Extension not connecting**: ensure `claude` CLI is on `PATH` and authenticated
- **IDE MCP tools not available**: restart VS Code after installing the extension
- **Slow file picker**: VS Code's file indexing may need to finish; try again in a moment

---

## 13. Claude Code on the Web

Claude Code on the web runs sessions in Anthropic-managed cloud VMs accessed via `claude.ai/code`. Unlike Remote Control, the entire session runs in the cloud.

### Starting a Web Session

Navigate to `claude.ai/code` and click "New session" or start from the Claude app.

To connect a local session to the web UI, see [Remote Control](#11-remote-control).

### The `--remote` Flag

Use `--remote` when starting a CLI session that you intend to use via the web:

```bash
claude --remote "start task"
```

This registers the session at `claude.ai/code` where you can monitor and interact with it remotely.

### Diff View

The web interface shows file diffs inline. Approve or reject individual hunks.

### Teleport

Teleport transfers a local Claude Code session (including its conversation history and working directory) to the cloud:

```bash
# Start teleport from CLI
claude --teleport

# From inside a session
/teleport
```

**Teleport requirements:**

| Requirement | Details |
|---|---|
| Repository | Must be a GitHub repository (public or private) |
| Authentication | GitHub account connected to claude.ai |
| Repository access | Claude.ai app must have access to the repository |
| Subscription | Pro, Max, Team, or Enterprise |

After teleporting, the session continues on a cloud VM with the repository cloned. Your local session ends.

### Session Sharing

| Plan | Sharing capability |
|---|---|
| Pro / Max | Share read-only session link |
| Team / Enterprise | Share editable session; team members can send messages |

### Cloud Environment

Default VM image includes:
- Ubuntu 22.04
- Node.js 20, Python 3.11, Ruby 3.2, Go 1.21, Java 17, Rust 1.75
- Common build tools: make, cmake, gcc, clang
- Git, GitHub CLI (`gh`)
- Common utilities: curl, wget, jq, ripgrep, fd

The VM does not have access to your local MCP servers, local filesystem, or local tools.

### Setup Scripts vs SessionStart Hooks

| | Setup script | SessionStart hook |
|---|---|---|
| When it runs | Once when the VM is provisioned | Every session start |
| Use for | Install dependencies, clone repos, configure environment | Initialize context, read state, send initial prompt |
| Persists | Yes (VM persists until session ends) | No (runs each time) |
| Location | `claude.ai/code` project settings | `.claude/settings.json` hooks config |

### Network Access

Web sessions have access to the internet. Allowlisted domains include npm, PyPI, GitHub, common CDNs, and cloud provider APIs. Custom domain allowlisting available on Enterprise plans.

### GitHub Proxy

Web sessions access GitHub via a Claude.ai proxy that uses your connected GitHub credentials. Direct git operations work without additional setup.

### Security Model

- Each session runs in an isolated VM
- VMs are destroyed after the session ends
- No data persists between sessions unless committed to GitHub
- No access to other users' sessions

### Dependency Management Limitations

- No persistent package caches between sessions; `npm install` runs fresh each time
- Large dependency installs can take significant time
- Consider committing `node_modules` or using a setup script that installs before the session starts

---

## 14. Chrome Integration

The Claude Code Chrome extension lets Claude interact with web pages: read content, click elements, fill forms, run console commands, and take screenshots.

### Prerequisites

- Claude Code CLI installed
- Chrome or Edge browser
- Claude Code Chrome extension installed from the Chrome Web Store

### Starting Chrome Integration

**From CLI:**

```bash
claude --chrome
```

**From inside a session:**

```
/chrome
```

**From VS Code extension:**

```
@browser
```

The `@browser` mention in VS Code includes the current Chrome tab's content in context.

### Example Workflows

**Debug a local web app:**
```
"Open http://localhost:3000/dashboard and check the browser console for errors"
```

**Test a form:**
```
"Fill out the signup form at http://localhost:3000/signup with test data and submit it"
```

**Extract data from a page:**
```
"Go to the GitHub repository page and extract all open PR titles and authors"
```

**Google Docs editing:**
```
"Open my Google Doc at [url] and add a section on deployment instructions"
```

**Multi-site comparison:**
```
"Compare the pricing pages at competitor-a.com and competitor-b.com"
```

### How It Works

Claude Code communicates with the Chrome extension via native messaging. The extension exposes tools for:
- `chrome.navigate(url)` — navigate to a URL
- `chrome.click(selector)` — click an element
- `chrome.fill(selector, value)` — fill a form field
- `chrome.evaluate(script)` — run JavaScript in the page context
- `chrome.screenshot()` — take a screenshot
- `chrome.getContent()` — get page HTML/text

### Native Messaging Host Paths

The native messaging host must be registered for Chrome to communicate with Claude Code.

**macOS Chrome:** `~/Library/Application Support/Google/Chrome/NativeMessagingHosts/`

**macOS Edge:** `~/Library/Application Support/Microsoft Edge/NativeMessagingHosts/`

**Linux Chrome:** `~/.config/google-chrome/NativeMessagingHosts/`

**Linux Edge:** `~/.config/microsoft-edge/NativeMessagingHosts/`

**Windows Chrome:** `HKCU\Software\Google\Chrome\NativeMessagingHosts\`

**Windows Edge:** `HKCU\Software\Microsoft\Edge\NativeMessagingHosts\`

The installer sets these up automatically. If Chrome integration fails, verify the manifest JSON file exists at the appropriate path.

### Troubleshooting

- **"Chrome extension not found"**: install the extension from the Chrome Web Store
- **"Native messaging host not registered"**: re-run `claude --chrome` which triggers registration, or reinstall Claude Code
- **Extension not responding**: restart Chrome after installing the extension
- **Actions failing on dynamic pages**: tell Claude to wait for elements with `"wait for the page to fully load"`

---

## 15. Monitoring and OpenTelemetry

Claude Code supports OpenTelemetry (OTEL) for exporting metrics, traces, and events to your observability stack.

### Enabling Telemetry

```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
```

Without this variable set, no telemetry data is exported.

### Configuration Environment Variables

| Variable | Description | Default |
|---|---|---|
| `CLAUDE_CODE_ENABLE_TELEMETRY` | Enable telemetry export | (disabled) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP gRPC or HTTP endpoint | — |
| `OTEL_EXPORTER_OTLP_HEADERS` | Headers for OTLP requests (e.g., auth) | — |
| `OTEL_EXPORTER_PROMETHEUS_PORT` | Expose Prometheus metrics on this port | — |
| `OTEL_METRICS_EXPORT_INTERVAL` | Export interval in milliseconds | 60000 |
| `OTEL_LOG_LEVEL` | Logging level for OTEL SDK itself | `warn` |
| `OTEL_RESOURCE_ATTRIBUTES` | Static key=value attributes for all telemetry | — |

### Metrics

| Metric | Type | Description |
|---|---|---|
| `claude_code.session.count` | Counter | Number of sessions started |
| `claude_code.lines_of_code.changed` | Counter | Lines added/removed across edits |
| `claude_code.pull_requests.created` | Counter | PRs created via Claude Code |
| `claude_code.commits.created` | Counter | Commits created via Claude Code |
| `claude_code.cost.usage` | Counter | Estimated API cost in USD |
| `claude_code.tokens.usage` | Counter | Token consumption (input/output/cache) |
| `claude_code.active_time` | Counter | Active session time in milliseconds |
| `claude_code.code_edit_tool.usage` | Counter | Uses of file edit tools |

Most metrics include dimension attributes: `session_id`, `model`, `project_path`, `user_email`.

### Events

| Event | Description |
|---|---|
| `user_prompt` | User sent a message |
| `tool_result` | A tool call completed |
| `api_request` | A request was made to the Anthropic API |
| `api_error` | An API request failed |
| `tool_decision` | User approved or rejected a tool call |

### Controlling Cardinality

High-cardinality attributes (like `session_id`) can cause metric explosion in some backends. To reduce cardinality:

```bash
# Drop high-cardinality dimensions
export OTEL_RESOURCE_ATTRIBUTES="service.name=claude-code,team=engineering"
```

Configure your OTEL collector to drop `session_id` from metrics if needed.

### Multi-Team Configuration

Use `OTEL_RESOURCE_ATTRIBUTES` to tag telemetry by team:

```bash
export OTEL_RESOURCE_ATTRIBUTES="service.name=claude-code,team=backend,env=production"
```

### Example Configurations

**Console output (debugging):**

```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_TRACES_EXPORTER=console
export OTEL_METRICS_EXPORTER=console
```

**OTLP to Grafana Cloud:**

```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp-gateway-prod-us-central-0.grafana.net/otlp"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic <base64-encoded-credentials>"
```

**Prometheus scrape endpoint:**

```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_EXPORTER_PROMETHEUS_PORT=9090
# Prometheus scrapes http://localhost:9090/metrics
```

**Dynamic auth headers** (for rotating tokens):

```bash
# Use a helper script that outputs headers
export OTEL_EXPORTER_OTLP_HEADERS="$(get-otel-token.sh)"
```

### Recommended Backends

- **Prometheus + Grafana**: metrics and dashboards
- **Jaeger** or **Tempo**: distributed traces
- **OpenTelemetry Collector**: fan-out, filtering, sampling before sending to backends
- **Datadog**, **New Relic**, **Honeycomb**: all support OTLP ingestion

---

## 16. Server-Side Compaction API

The Compaction API (beta) provides server-side conversation summarization for long-running agentic pipelines, replacing the full conversation history with a compact summary.

### Beta Header

All Compaction API requests require:

```
anthropic-beta: compact-2026-01-12
```

### Basic Usage

```python
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=8096,
    messages=[...],  # long conversation history
    betas=["compact-2026-01-12"],
    compact=True
)
```

### Compaction Response

When compaction occurs, the response includes a `compact_20260112` block:

```json
{
  "type": "message",
  "content": [
    {
      "type": "compact_20260112",
      "summary": "The conversation covered X, Y, Z. The current state is...",
      "compacted_messages": 47
    },
    {
      "type": "text",
      "text": "Claude's actual response..."
    }
  ]
}
```

### Configuration Parameters

| Parameter | Type | Description |
|---|---|---|
| `compact` | bool | Enable compaction for this request |
| `compact_trigger_tokens` | int | Compact when context exceeds this many tokens |
| `compact_instructions` | string | Custom instructions for the summary (e.g., "always preserve the list of files modified") |
| `pause_after_compaction` | bool | Stop after compacting and return the summary for inspection |
| `total_token_budget` | int | Hard cap on total tokens across the entire conversation |

### Trigger Threshold

```python
response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=8096,
    betas=["compact-2026-01-12"],
    compact=True,
    compact_trigger_tokens=50000,  # compact when context > 50K tokens
    compact_instructions="Always preserve: current task, file paths modified, pending steps"
)
```

### `pause_after_compaction`

Use this to inspect the summary before continuing:

```python
response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=8096,
    betas=["compact-2026-01-12"],
    compact=True,
    pause_after_compaction=True,
    messages=long_history
)

if response.stop_reason == "compacted":
    summary_block = next(b for b in response.content if b.type == "compact_20260112")
    print("Summary:", summary_block.summary)
    # Optionally edit the summary, then continue with it as the new history
```

### Working with Compaction Blocks

The compacted summary should replace the previous message history when continuing:

```python
def continue_after_compaction(response, new_user_message):
    compact_block = next((b for b in response.content if b.type == "compact_20260112"), None)
    if compact_block:
        # Use only the summary as history
        messages = [
            {"role": "assistant", "content": [compact_block]},
            {"role": "user", "content": new_user_message}
        ]
    else:
        messages = [...existing_history..., {"role": "user", "content": new_user_message}]
    return messages
```

### Prompt Caching with Compaction

Compaction works alongside prompt caching. Cache the compacted summary to avoid re-processing it:

```python
messages = [
    {
        "role": "assistant",
        "content": [
            {
                "type": "compact_20260112",
                "summary": "...",
                "cache_control": {"type": "ephemeral"}  # cache the summary
            }
        ]
    }
]
```

### Usage Tracking

The response includes an `iterations` array showing token usage across compactions:

```json
{
  "usage": {
    "input_tokens": 2100,
    "output_tokens": 450,
    "iterations": [
      { "input_tokens": 95000, "output_tokens": 2000 },
      { "input_tokens": 2100, "output_tokens": 450 }
    ]
  }
}
```

---

## 17. Agent Skills API

Agent Skills are reusable instruction packages that can be attached to API requests to extend Claude's capabilities. They are distinct from Claude Code skills (which are local markdown files) and operate at the API level.

### Architecture: Three-Level Progressive Loading

Skills are loaded lazily to minimize context overhead:

| Level | Loaded when | Content |
|---|---|---|
| Metadata | Always | Name, description (max 1024 chars), skill ID |
| Instructions | When the skill is first needed | Full prompt/instructions |
| Resources | When specific resources are accessed | Files, code, datasets |

Claude sees skill metadata at all times. Instructions and resources are fetched on demand.

### Pre-Built Skills

| Skill | Description |
|---|---|
| `pptx` | Create and edit PowerPoint presentations |
| `xlsx` | Create and edit Excel spreadsheets |
| `docx` | Create and edit Word documents |
| `pdf` | Read and extract content from PDFs |

### Using Pre-Built Skills

```python
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    betas=["agent-skills-2025-05-01"],
    skills=[{"type": "pptx"}, {"type": "xlsx"}],
    messages=[
        {
            "role": "user",
            "content": "Create a quarterly results presentation with 5 slides"
        }
    ]
)
```

### Custom Skills via `/v1/skills` API

Create a custom skill:

```python
skill = client.skills.create(
    name="run_python",           # max 64 characters
    description="Execute Python code and return results",  # max 1024 characters
    instructions="When asked to run Python code, use the execute_python tool...",
    resources=[
        {
            "name": "example_script.py",
            "content": "# Example usage...",
            "content_type": "text/x-python"
        }
    ]
)

# Use the custom skill
response = client.beta.messages.create(
    model="claude-opus-4-6",
    betas=["agent-skills-2025-05-01"],
    skills=[{"type": "custom", "id": skill.id}],
    messages=[...]
)
```

### Skill Structure Requirements

| Field | Max length | Required |
|---|---|---|
| `name` | 64 characters | Yes |
| `description` | 1024 characters | Yes |
| `instructions` | No hard limit | No |
| `resources` | Varies by surface | No |

### Security Considerations

- Skills run in the API's execution environment, not your local machine
- Custom skills are scoped to your API key (not visible to other users by default)
- Resources included in skills are accessible to Claude during the session; do not include secrets
- Skill sharing scope: individual API key only (cannot be shared across organization by default)

### Cross-Surface Availability

Skills are available when using:
- The Anthropic API directly (full support)
- Claude Code on the web (pre-built skills only)
- Claude mobile app (limited: metadata and instructions; no filesystem resources)

Local Claude Code sessions support their own skill system (SKILL.md files) which is separate from and more capable than the API-level skills.

### Runtime Environment

When skills interact with files, they use the session's VM environment:
- Pre-built Office skills write files to the VM filesystem
- Files can be retrieved via the API's file handling endpoints
- No persistent storage between API calls unless using file IDs

---

## 18. Platform Release Notes

A summary of major Claude Code and Claude API releases.

### 2026

**March 2026**
- Remote Control GA: connect local sessions to `claude.ai/code` and mobile apps
- Claude Code VS Code extension GA with plugin marketplace
- Chrome integration GA: `--chrome` flag and `@browser` VS Code mention
- Agent teams (experimental): peer-to-peer multi-session coordination

**February 2026**
- Compaction API beta (`compact-2026-01-12`): server-side conversation summarization
- Subagents: custom subagent definitions in `.claude/agents/`
- Git worktrees: `--worktree`/`-w` flag for parallel isolated sessions

**January 2026**
- Claude Code 1.0 GA release
- Skills system GA: SKILL.md, bundled skills, `context: fork`
- Hooks GA: all event types, http/prompt/agent hook types
- Path-scoped rules in `.claude/rules/`

### 2025

**November–December 2025**
- Plan mode (`--permission-mode plan`, `Shift+Tab`)
- Checkpoints and `/rewind` command
- Extended thinking with `/effort` command
- Claude Code on the web beta
- OpenTelemetry monitoring support

**September–October 2025**
- Agent Skills API (`/v1/skills`, pre-built PPTX/XLSX/DOCX/PDF skills)
- Auto memory (CLAUDE.md and MEMORY.md system)
- Session management: `--fork-session`, improved session picker

**July–August 2025**
- Hooks (initial): `PreToolUse`, `PostToolUse`, `Stop` events
- MCP per-server context display (`/mcp`)
- `--headless` mode for CI/CD pipelines

**May–June 2025**
- Claude Code public beta launch
- claude.ai OAuth authentication for Claude Code
- Initial VS Code extension

**Pre-May 2025**
- Claude 3.5 Sonnet, Haiku, Claude 3 Opus model releases
- Extended context (200K tokens)
- Tool use GA
- Vision capabilities GA

### Model Availability

Current models (as of March 2026):

| Model | Alias | Best for |
|---|---|---|
| Claude Opus 4.6 | `claude-opus-4-6` | Complex reasoning, agentic tasks |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | Balanced capability and speed |
| Claude Haiku 4.5 | `claude-haiku-4-5` | Fast, lightweight tasks |

All Claude 4 models support adaptive reasoning (extended thinking) and 200K context windows.
