---
name: code-review
description: Review code changes for quality, security, and correctness. Use when the user says "review this PR", "review these changes", "check my code", "look at what I changed", or after implementing a feature. Produces a severity-organized report.
argument-hint: "[file path, branch, or PR number]"
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash(git *)
---

# Code Review

Produce a severity-organized review report covering security, correctness, and quality for code changes.

## Goal
Identify issues in code changes, organized by severity (Critical > Warnings > Suggestions), with specific file:line references and fix suggestions for every finding. Done when the report is presented to the user.

## Context
Before reviewing, read CLAUDE.md and any linter/formatter config files (.eslintrc, pyproject.toml, .prettierrc, etc.) to understand project conventions. Do not flag style issues already handled by configured tooling.

## Process

### Step 1: Identify Changes
- If `$ARGUMENTS` specifies a file, branch, or PR: use that scope
- If `$ARGUMENTS` is empty: run `git diff main...HEAD`. If that returns nothing, ask: "What should I review — a branch, specific files, or uncommitted changes?"
- Identify all modified files and understand the scope

**CHECKPOINT:** Present the identified files and diff scope. Confirm this is the correct review target before proceeding.

### Step 2: Understand Context
- Read the modified files fully (not just the diff)
- Understand what the code is supposed to do
- Check for related test files

### Step 3: Review Checklist

**Critical (must fix before merge):**
- Security vulnerabilities (injection, XSS, exposed secrets, missing auth checks)
- Data loss risks (destructive operations without confirmation, missing transactions)
- Race conditions or concurrency issues
- Breaking changes to public APIs without migration path

**Warnings (should fix):**
- Missing error handling for external calls (network, file I/O, DB)
- Missing input validation at system boundaries
- Duplicated logic that should be shared
- Performance issues (N+1 queries, unnecessary allocations in loops)
- Missing or inadequate test coverage for new behavior

**Suggestions (nice to have):**
- Naming improvements for clarity
- Simplification opportunities
- Better patterns available in the framework

### Step 4: Report
For each finding:
1. **File and line reference**: `path/to/file.ts:42`
2. **What's wrong**: One sentence
3. **Why it matters**: Impact if not fixed
4. **How to fix**: Specific suggestion with code example

Organize findings by severity: Critical first, then Warnings, then Suggestions.

## Output
Report is presented inline in the conversation, organized by severity. Offer to save to `.claude/memory/review-YYYY-MM-DD.md` if the user wants a record.

## What NOT to Flag
- Style issues handled by linters/formatters
- Opinions about code organization without concrete benefit
- "I would have done it differently" without a clear improvement
- Missing documentation on self-explanatory code
