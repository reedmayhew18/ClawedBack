# Claude Code: Workflows and Automation

A comprehensive reference covering the `/loop` command, remote control, CI/CD integration, refactoring strategies, the Ralph Loop, automation patterns, and hooks.

---

## Table of Contents

1. [The /loop Command](#the-loop-command)
2. [Remote Control](#remote-control)
3. [Channels (Event-Driven Sessions)](#channels)
4. [CI/CD Integration](#cicd-integration)
5. [Legacy Codebase Refactoring](#legacy-codebase-refactoring)
6. [Automated Refactoring Strategies](#automated-refactoring-strategies)
7. [The Ralph Loop](#the-ralph-loop)
8. [Hooks: Deterministic Automation](#hooks-deterministic-automation)
9. [The Orchestra Research Framework](#the-orchestra-research-framework)

---

## The /loop Command

### What It Does

`/loop` creates a session-level scheduler. You give it a prompt and a cadence; it queues that prompt to repeat at the interval you specify without manual re-triggering. It functions like an in-process cron job — no crontab setup required.

Announced in early 2026, `/loop` can schedule recurring tasks for **up to 3 days**.

### Basic Syntax

```
/loop "check for new TODO comments and report any added in the last commit" --interval 15m
```

With a cron expression for precise scheduling:

```
/loop "run the test suite and summarize failures" --cron "0 9 * * 1-5"
```

**Flags:**
- `--interval` — accepts values like `5m`, `1h`, `30s`, `24h`
- `--cron` — standard five-field cron expression
- `--times` — cap the number of cycles before the loop terminates
- `/loop --cancel` — stop the currently running loop

### Real-World Use Cases

From the official announcement examples:

```
/loop babysit all my PRs. Auto-fix build issues and when comments come in,
      use a worktree agent to fix them

/loop every morning use the Slack MCP to give me a summary of top posts
      I was tagged in
```

Other high-value targets:

```
# Continuous code quality monitoring
/loop "review files changed in the last git commit and flag any functions over
       50 lines or missing error handling" --interval 30m

# Automated test failure analysis
/loop "run npm test and if any tests fail, identify the most likely cause
       based on recent code changes" --interval 2h

# Daily commit digest
/loop "summarize all commits from the last 24 hours in plain language,
       grouped by feature area" --cron "0 8 * * 1-5"

# Dependency and security monitoring
/loop "run npm audit and list any high or critical vulnerabilities,
       with recommended actions" --interval 24h

# Documentation drift detection
/loop "compare the API documentation in /docs with current function
       signatures in /src/api and report any mismatches" --interval 1d

# Structured output for downstream parsing
/loop "check for deprecated imports and output ONLY a JSON array of
       file paths, no other text" --interval 1h
```

### Key Limitations

**Session dependency** — Loops stop when the terminal session closes. The loop is process-bound, not system-bound. Use `tmux` or `screen` to persist:

```bash
# Keep session alive with tmux
tmux new -s claude-loop
claude
# run /loop command, then detach with Ctrl+B, D

# Or with screen
screen -S claude-session
claude
# run /loop command, then detach with Ctrl+A, D
```

**Context accumulation** — Each cycle runs within the existing session context, which grows over time. Use `/compact` periodically. For long-running loops, consider whether fresh-session-per-cycle produces better results.

**API costs** — Every cycle consumes tokens. Estimate per-cycle cost with `/cost` after a manual run, then multiply:

> A task costing $0.05/run at 5-minute intervals = $14.40/day. Match interval to actual value.

**No native alerting** — Output goes to terminal only. To get alerts, pipe output through a script that calls a webhook or sends a Slack message when specific keywords appear.

**Output reliability** — Responses are non-deterministic. For machine-parseable output, always specify the format explicitly in the prompt.

### Combining /loop with System Cron

For tasks that must survive reboots or run unattended on remote servers, use system cron with Claude's non-interactive mode:

```bash
#!/bin/bash
# claude-daily-check.sh
cd /path/to/your/project
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> /var/log/claude-daily.log
claude -p "summarize all commits from the last 24 hours by feature area" >> /var/log/claude-daily.log 2>&1
```

```bash
chmod +x claude-daily-check.sh
crontab -e
# Add:
0 8 * * 1-5 HOME=/home/yourusername /path/to/claude-daily-check.sh
```

**Authentication in cron:** Set `HOME` explicitly. Claude stores credentials in `~/.config/claude/` and needs the environment variable to find them.

**Log rotation:**

```
# /etc/logrotate.d/claude-tasks
/var/log/claude-task.log {
    daily
    rotate 7
    compress
    missingok
}
```

---

## Remote Control

`/remote-control` lets you connect Claude Code web or the Claude mobile app to a running local session.

### How to Use It

**Start a new session with remote control:**

```bash
cd /path/to/your/project
claude remote control
# Shows a URL — press spacebar for a QR code to scan with your phone
```

**Enable remote control inside an existing session:**

```
/remote control
```

The URL is provided for convenience, but since Claude Code is tied to your Claude account, you can also access it from the Claude mobile app by navigating to your device's session.

### What Remote Control Provides

- **Same tools and file system** — everything runs on your machine; nothing moves to the cloud
- **Real-time sync** — typing in the mobile app appears in your terminal instantly
- **Spawn mode** — create new sessions remotely from Claude web or mobile by selecting the environment button and choosing your device

**Availability:** Mac Team and Enterprise users initially; rolling out to Pro and Max plan users.

### Configuration

To enable remote control for all sessions automatically:

```
/config
# Enable remote control for all sessions
```

### Comparison with Channels

| Feature | Remote Control | Channels |
|---|---|---|
| Mode | Interactive — you review and control | Reactive — Claude responds to events automatically |
| Use case | Continue a session from your phone | CI alerts, webhooks, Telegram bot messages |
| Session state | Warm, continuous | Warm, continuous |

These features pair well together: remote control for human interaction, channels for automated event handling.

---

## Channels

Channels allow external events to be sent directly into a running Claude Code session. This creates **always-on, warm sessions** that react to infrastructure events rather than waiting for human input.

### What Channels Solve

Without channels, handling a CI failure requires: see failure → open terminal → paste logs → wait for response. With channels, the CI webhook fires, the channel receives it, Claude already has full context, and can fix and push before you reach your laptop.

### Event Sources

- Webhooks (CI systems, monitoring tools)
- Bot messages from Telegram or Discord
- Cron jobs
- Log file watchers
- Health checks and test runners
- Custom application events

### Architecture

Channels work through an MCP plugin that runs as a subprocess wherever your Claude Code instance runs. It bridges external events to the active session while maintaining session continuity.

### Setting Up a Telegram Channel

```bash
# 1. Create a bot via BotFather on Telegram
# Search for "BotFather" → /newbot → give it a name → copy the access token

# 2. Install the Telegram plugin in Claude Code
/plugins telegram-plugins-official
# Install for user scope

# 3. Configure with your token
/telegram:configure
# Paste your bot token

# 4. Restart Claude Code, then run
/channels telegram

# 5. Lock down to your account only (critical security step)
/telegram access policy allow list
```

### Example: CI Auto-Fix Loop

```
Push code → CI fails → webhook fires → channel receives failure log →
Claude (with codebase context) analyzes → applies fix → pushes fix →
CI passes
```

### Comparison with Headless Mode

- **Headless (`-p` flag):** Cold session — starts fresh, returns result, exits
- **Channels:** Warm session — Claude has accumulated context, can handle cascading events

---

## CI/CD Integration

### Why Claude Code in CI/CD

Traditional CI scripts are deterministic but rigid — grep for version bumps, static regex for API validation. When you refactor a monorepo, those scripts break silently. Claude Code brings semantic understanding: it knows what constitutes a breaking change, can infer service dependencies from import paths, and generates contextual deployment plans.

The pattern: run Claude Code as a containerized step in your pipeline, feed context via environment variables, and have it return structured JSON that subsequent steps act on — fail the build, trigger a canary deployment, or post to Slack.

### Container Configuration

```dockerfile
# Dockerfile.claude-cicd
FROM node:20-alpine

RUN npm install -g @anthropic-ai/claude-code

WORKDIR /workspace

ENV CLAUDE_CODE_CI_MODE=true
ENV CLAUDE_CODE_QUIET=true

ENTRYPOINT ["claude"]
```

```bash
docker build -f Dockerfile.claude-cicd -t claude-cicd .
docker run -e ANTHROPIC_API_KEY=sk-ant-... claude-cicd --help
```

### GitHub Actions Integration

```yaml
# .github/workflows/claude-validation.yml
name: Claude Code Validation

on:
  workflow_call:
    inputs:
      skill_name:
        required: true
        type: string
      parameters:
        required: false
        type: string
        default: '{}'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for change analysis

      - name: Run Claude Code Skill
        uses: docker://claude-cicd:latest
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          args: |
            skill "${{ inputs.skill_name }}" \
            params '${{ inputs.parameters }}' \
            output /workspace/claude-output.json

      - name: Parse Claude Output
        id: parse
        run: |
          echo "claude_result=$(cat /workspace/claude-output.json)" >> $GITHUB_OUTPUT

      - name: Fail on Breaking Changes
        if: fromJson(steps.parse.outputs.claude_result).hasBreakingChanges
        run: |
          echo "Breaking changes detected: ${{ fromJson(steps.parse.outputs.claude_result).details }}"
          exit 1
```

Calling from your main CI pipeline:

```yaml
# .github/workflows/ci.yml
jobs:
  check-breaking-changes:
    uses: ./.github/workflows/claude-validation.yml
    with:
      skill_name: "api-breaking-change-detector"
      parameters: '{"baseBranch": "main", "changedFiles": "${{ needs.changes.outputs.changed_files }}"}'
```

### GitLab CI Integration

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - test
  - deploy

claude:validate:api:
  stage: validate
  image: claude-cicd:latest
  variables:
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
  script:
    - |
      claude --skill api-breaking-change-detector \
        --params "{\"baseBranch\": \"$CI_DEFAULT_BRANCH\"}" \
        --output claude-output.json
      if jq -e '.hasBreakingChanges' claude-output.json > /dev/null; then
        echo "Breaking API changes detected: $(jq -r '.details' claude-output.json)"
        exit 1
      fi
  artifacts:
    reports:
      dotenv: claude-output.env
    paths:
      - claude-output.json
```

### Practical CI/CD Workflows

**Workflow 1: Intelligent Test Runner**

Instead of running all tests on every commit, run only tests impacted by changed files:

```yaml
jobs:
  determine-tests:
    runs-on: ubuntu-latest
    outputs:
      test-matrix: ${{ steps.claude.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
      - id: claude
        run: |
          CHANGED_FILES=$(git diff --name-only HEAD~1)
          MATRIX=$(claude --skill test-selector \
            --params "{\"changedFiles\": \"$CHANGED_FILES\", \"testPattern\": \"**/*.test.ts\"}" \
            --output - | jq -c '.testMatrix')
          echo "matrix=$MATRIX" >> $GITHUB_OUTPUT

  run-tests:
    needs: determine-tests
    strategy:
      matrix: ${{ fromJson(needs.determine-tests.outputs.test-matrix) }}
    steps:
      - uses: actions/checkout@v4
      - run: npm test ${{ matrix.testFile }}
```

**Workflow 2: Automated Release Notes**

```yaml
jobs:
  generate-notes:
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Generate Release Notes
        run: |
          claude --skill release-notes-generator \
            --params "{\"fromTag\": \"${{ github.event.inputs.fromTag }}\", \"toTag\": \"${{ github.event.inputs.toTag }}\"}" \
            --output release-notes.md
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          body_path: release-notes.md
```

**Workflow 3: Security Scan Orchestration**

```yaml
security-scan:
  stage: validate
  script:
    - trivy image --format json $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA > trivy.json
    - sonar-scanner -Dsonar.analysis.mode=preview > sonar.json
    - |
      claude --skill security-triage \
        --params "{\"trivyReport\": \"trivy.json\", \"sonarReport\": \"sonar.json\"}" \
        --output triage-result.json
      if jq -e '.criticalIssues > 0' triage-result.json; then
        exit 1
      fi
  artifacts:
    reports:
      security: triage-result.json
```

Claude correlates findings across tools, eliminates duplicates, and prioritizes by exploitability.

### Handling Secrets and Permissions

```yaml
# GitHub Actions — inject secrets as environment variables
- name: Run Claude with Secrets
  run: claude --skill deploy-skill
  env:
    DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

**Least-privilege GitLab configuration:**

```yaml
claude-job:
  before_script:
    - export ANTHROPIC_API_KEY=${CI_JOB_TOKEN_LIMITED}
  variables:
    GIT_STRATEGY: fetch  # No push access
    CLAUDE_CODE_READONLY: true
```

### Troubleshooting CI/CD

| Issue | Cause | Fix |
|---|---|---|
| Claude hangs | Waiting for interactive prompts | Add `--quiet --non-interactive` flags |
| MCP server fails in container | Missing deps or wrong Node version | Build dedicated image with `npm ci --only=production` |
| Rate limiting | Too many parallel API calls | Use `p-queue` with `concurrency: 1` |
| Skills not found | Relative paths in MCP config | Use absolute paths; checkout skills repo in CI step |

---

## Legacy Codebase Refactoring

*Based on a developer's account of refactoring a 50k-line Django monolith in 3 weeks (estimated 2-3 months without Claude Code).*

### The Core Problem

Claude Code has no idea what your code is *supposed* to do — only what it *does* do. For legacy code, this is dangerous. The solution is to lock down existing behavior before touching a single line.

### Step 1: Characterization Tests First

Do not ask Claude to refactor anything at first. Ask it to write tests that capture current behavior:

```
"Generate minimal pytest characterization tests for [module]. Focus on capturing
current outputs given realistic inputs. No behavior changes, just document what
this code actually does right now."
```

This feels slow — you're not "making progress" yet. But these tests are what let you refactor fearlessly. Spend the first 4 days generating characterization tests for the modules you're most afraid to touch.

Every time Claude makes a change, run tests. Passing = behavior preserved. Failing = regression caught before prod.

### Step 2: Set Up CLAUDE.md with Hard Rules

CLAUDE.md files cascade hierarchically. If you have `root/CLAUDE.md` and `apps/billing/CLAUDE.md`, both load when Claude touches billing code. Use this for module-specific constraints.

```markdown
## Build Commands

- `python manage.py test apps.billing.tests` — Run billing tests
- `python manage.py test --parallel` — Run full test suite
- `flake8 apps/` — Run linter

## Architecture Overview

Django monolith, ~50k LOC. Core modules: billing, auth, inventory, notifications.
Billing and auth are tightly coupled (legacy decision). Inventory is relatively isolated.
Database: PostgreSQL. Cache: Redis. Task queue: Celery.

## Refactoring Guidelines

- IMPORTANT: Always run relevant tests after any code changes
- Prefer incremental changes over large rewrites
- When extracting methods, preserve original function signatures as wrappers initially
- Document any behavior changes in commit messages

## Hard Rules

- DO NOT modify files in apps/auth/core without explicit approval
- DO NOT change any database migration files
- DO NOT modify the BaseModel class in apps/common/models.py
- Always run tests before reporting a task as complete
```

Every codebase has load-bearing walls — code that looks ugly but handles a critical edge case nobody fully understands. Explicitly name them as off-limits.

### Step 3: Incremental Refactoring with Continuous Verification

Break refactoring into small, specific tasks:

- "Extract the discount calculation logic from `Invoice.process()` into a separate method."
- "Rename all instances of `usr` to `user` in the auth module."
- "Remove the deprecated `payment_v1` endpoint and all code paths that reference it."

Each task gets its own prompt:

```
"Implement this refactoring step: [specific task]. After making changes, run
pytest tests/[relevant_test_file].py and confirm all tests pass. If any fail,
debug and fix before reporting completion."
```

This feels tedious but is far faster than a big-bang refactor that breaks 47 things at once.

### Step 4: AI-Assisted Code Review

Even with tests passing, you can miss security issues, performance antipatterns, and subtle logic errors. After each refactoring chunk: commit, push, run an AI code review tool (CodeRabbit, or ask Claude itself to review the diff as a separate task), fix flagged issues, push again.

One practitioner reported an AI reviewer catching a SQL injection vulnerability Claude had introduced while "cleaning up" a database query.

### Where This Breaks Down

- **Context limits:** Performance degrades well before the 200k token limit. Aim to stay under 25-30k tokens per session.
- **Hallucinated APIs:** Claude will sometimes use methods that don't exist. Characterization tests catch most of this.
- **Architectural decisions:** Claude can execute a refactoring plan beautifully. It cannot tell you whether that plan makes sense for where the codebase is headed. That judgment remains human work.

### Handoff Documents

For multi-session refactors, maintain handoff documents — markdown files summarizing progress, decisions made, and next steps. One effective structure (from community practice):

```
/planning/refactor/
  ./001-tdd/
    ./001-initial.md        — written by you
    ./002-thoughts.md       — LLM output
    ./003-plan.md           — LLM output, refined
    ./100-review.md         — review of implementation
  ./002-services/
    ./001-handoff.md        — generated when 001 finishes
```

The handoff doc should include: what changed, why, what was explicitly refused, which tests prove behavior is preserved, and any known unknowns.

---

## Automated Refactoring Strategies

Beyond manual step-by-step refactoring, Claude Code supports automated approaches:

### 1. Architecture Skill

An "Improve Codebase Architecture" skill can:
- Explore the codebase and surface areas Claude finds confusing (tightly coupled modules, pure functions hiding bugs)
- Present a list of refactoring candidates
- Once you select one, spawn multiple sub-agents in parallel — each producing a different interface design for the module
- Compare the designs, recommend the strongest hybrid, and automatically generate a GitHub issue for the refactor

### 2. Autonomous TDD via the Ralph Loop

Prompt an autonomous Ralph loop with a TDD skill to run a continuous "red, green, refactor" cycle:
1. Write a failing test
2. Write the exact code needed to make it pass
3. Look for refactoring candidates
4. Move to the next task

### 3. Plan Mode for Complex Refactors

For large migrations or complex refactors, do not let the AI execute code immediately. Switch to Plan Mode with `Shift+Tab`. Claude uses read-only operations to analyze your implementation and draft a comprehensive refactoring plan. Review and edit the plan in your text editor before approving execution. Always ask Claude to refactor in small, testable increments.

---

## The Ralph Loop

The Ralph Loop is an official Claude Code plugin (named after Ralph Wiggum from The Simpsons) that enables fully autonomous coding or task pipelines.

### How It Works

Instead of Claude running once and waiting for input, the Ralph Loop runs a continuous bash `while` loop. As files are built and modified, it repeatedly feeds the updated files and tasks into a fresh context window, working through the problem on its own until it completely nails the task.

The constant context refresh prevents **context rot** — where Claude forgets instructions during long, memory-heavy sessions.

### Setup

**1. Create a Product Requirements Document (`prd.json`)**

Before running the loop, define strict user stories and clear acceptance criteria:

```json
{
  "user_stories": [
    {
      "id": "POST-001",
      "description": "Write a LinkedIn post under 200 words about topic X",
      "acceptance_criteria": [
        "Post is under 200 words",
        "No banned words from banned-words.md",
        "Status set to 'draft' in content calendar",
        "File saved to /output/drafts/post-001.md"
      ],
      "status": "pending"
    }
  ]
}
```

The loop creates its own verification tests from the acceptance criteria and will not stop until those specific conditions are met. It updates `status` to `"done"` as tasks complete.

**2. Install the Plugin**

```
/plugin install raw
```

**3. Run with Safety Limits**

```
/Ralph loop --max-iterations 10
```

Always set `--max-iterations`. Without it, the loop could run indefinitely on complex tasks, consuming substantial tokens.

### Common Use Cases

- **GitHub issue burning:** Break a PRD into individual GitHub issues. The Ralph Loop grabs an issue, writes the code, passes the tests, comments on the issue, closes it, moves to the next one.
- **TDD automation:** Prompt with a TDD skill for autonomous "red, green, refactor" cycles.
- **Batch content processing:** Feed a content calendar with specific acceptance criteria (under 200 words, no banned words). Walk away; return to a week's worth of content drafted, reviewed, and ready for approval.

### Ralph Loop vs. GSD Framework

| | Ralph Loop | GSD Framework |
|---|---|---|
| Role | Executor | Planner + Executor |
| Best for | Well-defined tasks with clear acceptance criteria | Large projects requiring scoping and phase breakdown |
| Example | "Write these 6 posts per the spec" | "Build a content strategy for Q2" |

---

## Hooks: Deterministic Automation

Hooks are shell commands that execute automatically at specific points in the development lifecycle. They require no AI reasoning tokens — they run mechanically, making them ideal for deterministic enforcement.

### The 8 Hook Event Types

Hooks live in `.claude/settings.json` under the `hooks` key.

**1. UserPromptSubmit** — Fires when you submit a prompt, before Claude processes it

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "echo 'Prompt submitted at $(date)' >> ~/.claude/prompt-log.txt"
      }]
    }]
  }
}
```

**2. PreToolUse** — Runs before Claude executes any tool. Use for validation and security

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "if [[ \"$CLAUDE_TOOL_INPUT\" == *\"rm -rf\"* ]]; then echo 'Dangerous command blocked!' && exit 2; fi"
      }]
    }]
  }
}
```

Exit code `2` blocks the action and feeds the reason back to the agent as context.

**3. PostToolUse** — Executes after successful tool completion. Use for auto-formatting

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "if [[ \"$CLAUDE_FILE_PATHS\" =~ \\.(ts|tsx)$ ]]; then prettier --write \"$CLAUDE_FILE_PATHS\"; fi"
      }]
    }]
  }
}
```

**4. Notification** — Fires when Claude sends permission requests or waits for input

```json
{
  "hooks": {
    "Notification": [{
      "hooks": [{
        "type": "command",
        "command": "osascript -e 'display notification \"Claude needs attention\" with title \"Claude Code\"'"
      }]
    }]
  }
}
```

**5. Stop** — Runs when Claude finishes responding

**6. SubagentStop** — Fires when a subagent finishes

**7. PreCompact** — Runs before context compaction. Use to back up session transcripts

```json
{
  "hooks": {
    "PreCompact": [{
      "hooks": [{
        "type": "command",
        "command": "cp ~/.claude/current-session.jsonl ~/.claude/backups/session-$(date +%s).jsonl"
      }]
    }]
  }
}
```

**8. SessionStart** — Executes when starting new sessions

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "git status > /tmp/claude-git-context.txt && echo 'Development context loaded'"
      }]
    }]
  }
}
```

### Hook Environment Variables

Hooks have access to:
- `CLAUDE_PROJECT_DIR` — current project directory
- `CLAUDE_FILE_PATHS` — files being modified
- `CLAUDE_TOOL_INPUT` — tool parameters (JSON)
- `CLAUDE_TOOL_NAME` — name of the tool being invoked (useful for audit logging)

### JSON Response Control

Hooks can return structured JSON for sophisticated control flow:

```python
import json

response = {
    "continue": True,          # Whether Claude should continue
    "feedback": "Check passed",
    "modify_prompt": False
}
print(json.dumps(response))
```

### Practical Hook Patterns

**Brand integrity / banned words:**

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "python ~/.claude/hooks/check-banned-words.py \"$CLAUDE_FILE_PATHS\""
      }]
    }]
  }
}
```

You don't need to write hooks by hand — ask Claude: *"Write a hook that checks every file edit against my banned words list and flags it if any are found."* Claude will write the script and add the configuration to `.claude/settings.json`. Verify with `/hooks` to see active hooks.

**Protect sensitive files from editing:**

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "if [[ \"$CLAUDE_FILE_PATHS\" == *\".env\"* ]]; then echo 'Cannot edit .env file' && exit 2; fi"
      }]
    }]
  }
}
```

**Post-compaction context renewal** (prevents "context rot" after compaction):

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "compact",
      "hooks": [{
        "type": "command",
        "command": "cat ~/.claude/context-essentials.md"
      }]
    }]
  }
}
```

This injects a "Context Essentials" file every time compaction occurs, ensuring the agent never forgets its core instructions.

**Audit logging for enterprise environments:**

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "echo \"$(date): Tool ${CLAUDE_TOOL_NAME} executed by ${USER}\" >> /var/log/claude-audit.log"
      }]
    }]
  }
}
```

### Simple Mental Model

- **Hooks** — What happens *automatically* after Claude acts (no AI tokens)
- **Skills** — How Claude *thinks* about a task (loaded into context when relevant)
- **Slash Commands** — What you *manually trigger* for repetitive tasks

---

## The Orchestra Research Framework

The Orchestra Research Framework is an open-source AI Research Skills Library designed to give AI coding agents (like Claude Code) the ability to autonomously conduct the full lifecycle of AI research — from brainstorming and literature surveys through running experiments and writing the final paper.

The library contains 86 specialized engineering and research skills organized into categories including ideation, literature review, experimentation, and writing.

### Ideation Layer

The "Research Brainstorming" skill uses a structured framework with 10 complementary lenses for discovering high-impact research directions (the specific lenses are not publicly documented in detail).

The paired "Creative Thinking" skill relies on cognitive science frameworks to generate genuinely novel ideas:
- **Bisociation** — connecting concepts from unrelated domains
- **Structure-mapping** — applying the relational structure of one domain to another
- **Constraint manipulation** — systematically relaxing or tightening constraints to explore the solution space

### Autoresearch Orchestration

The central "Autoresearch" layer automatically routes the AI to different domain skills as it plans and executes research, similar to the Conductor plugin pattern: Context → Spec & Plan → Implement → Verify.

This framework is one example of how Claude Code's skill and orchestration system can be applied to non-software domains — the same patterns (skills, sub-agents, acceptance criteria loops) that work for software development translate directly to research pipelines.
