---
name: git-workflow
description: Structured git workflow for commits, branches, and PRs. Use when the user says "commit", "create a PR", "new branch", "prepare for review", "ship this", or "push my changes". Safe, conventional git operations with checkpoints.
argument-hint: "[commit/pr/branch] [description]"
disable-model-invocation: true
allowed-tools: Bash
---

# Git Workflow

Safe, structured git operations with user checkpoints before irreversible actions.

## Goal
Ensure git operations are safe, conventional, and reviewable.
- **Commit done:** user-approved commit exists with conventional message and hash returned
- **Branch done:** correctly named branch created and checked out, confirmed to user
- **PR done:** branch pushed, PR created via `gh`, PR URL returned to user

## Dependencies
**Tools:** Bash (all git operations, `gh` CLI for PRs)
**CLI required:** `git` (always available), `gh` (GitHub CLI — required for PR command only; warn user if not installed)
**No MCP or external API required**

## Context
- Read `CLAUDE.md` for project-specific branch naming conventions before creating a branch
- Check `.github/pull_request_template.md` before drafting a PR body; use it as the template if present
- Check `.github/CODEOWNERS` or CI config if relevant for reviewer assignment

## Commands

### Commit: `/git-workflow commit [message]`
1. Run `git status` and `git diff --staged` to understand changes
2. Check for sensitive files (.env, credentials, secrets) — WARN and exclude if found
3. Determine which files to stage (never `git add -A` or `git add .` — stage specific files)
4. If no message provided, draft one:
   - Prefix: feat/fix/refactor/docs/test/chore
   - Focus on WHY, not WHAT (the diff shows what)
   - Under 72 chars for subject line

**CHECKPOINT:** Present staged file list and draft commit message. Do NOT commit until user approves.

5. Create the commit

### Branch: `/git-workflow branch [name]`
1. Run `git status` — warn if uncommitted changes exist; ask user to commit or stash before proceeding
2. Fetch latest from remote (`git fetch`)
3. Derive branch name: use provided name or propose one from context using convention `feat/description`, `fix/description`, `refactor/description`

**CHECKPOINT:** Show proposed branch name and source branch (e.g., `main`). Do NOT create the branch until user approves.

4. Create branch from main/master and switch to it
5. Output: "Created and switched to `branch-name` from `main`."

### PR: `/git-workflow pr`
1. Run `git status` — warn if uncommitted changes
2. Run `git log main..HEAD` to understand all commits on this branch
3. Run `git diff main...HEAD` for the complete diff
4. Draft PR with:
   - Short title (under 70 chars)
   - Summary section with 1-3 bullet points
   - Test plan checklist

**CHECKPOINT:** Show PR title, summary, and test plan. Do NOT push or create PR until user confirms.

5. Push branch with `-u` flag if not pushed
6. Create PR via `gh pr create`
7. Return the PR URL

## Output
- Commit: confirmation message with hash
- Branch: confirmation with branch name
- PR: the PR URL

## Safety Rules
- NEVER force push to main/master
- NEVER commit .env, credentials, API keys, tokens
- NEVER amend published commits without explicit request
- NEVER skip pre-commit hooks (--no-verify)
- Always stage specific files, not everything
- Always verify branch before pushing
