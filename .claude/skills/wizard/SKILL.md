---
name: wizard
description: 8-phase implementation methodology with built-in verification at each stage. Use for implementing features, fixing complex bugs, or any task where quality matters. Use when the user says "wizard mode", "do this properly", "production quality", or "full workflow".
argument-hint: "[task description or issue number]"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Wizard - 8-Phase Implementation

## Goal
Deliver a production-quality implementation with zero regressions. Success = all new tests pass, full test suite passes, linter clean, and user has reviewed and approved a complete diff summary.

## Dependencies
- Tools: Read, Write, Edit, Bash, Grep, Glob
- Requires a test runner (language-appropriate: pytest, jest, go test, etc.)
- Reads CLAUDE.md for project conventions at Phase 1

## Context
Reads CLAUDE.md and any linked specs or issues at Phase 1. References existing codebase patterns discovered during Phase 2 exploration.

A production-tested methodology that prevents common AI coding failures.

## Phase 1: Plan
- Read CLAUDE.md and any linked specs/issues
- Assess complexity: files affected, architectural impact, risk level
- Build structured task list before writing any code
- Present plan for user approval

## Phase 2: Explore
- Grep for every model, method, class, and constant you intend to use
- **Verify they actually exist** before referencing them
- Read related code to understand patterns and conventions
- This prevents hallucinated method chains and non-existent APIs

## Phase 3: Test First
- Write failing tests covering:
  - Happy path
  - Edge cases (null, empty, boundary values)
  - Error conditions
- Use mutation-resistant assertions (specific values, not truthiness)
- Run tests - they MUST fail
- Note the failing tests (don't modify them later to make them pass)

## Phase 4: Implement Minimum
- Write only the code needed to make tests pass
- No extra features, no premature abstractions
- No "while I'm here" improvements
- Keep the implementation as simple as possible

## Phase 5: Verify No Regression
- Run the broader test suite, not just new tests
- Catch unrelated breakage immediately
- Fix any regressions before moving forward

## Phase 6: Document
- Add inline comments only where logic isn't self-evident
- Update any relevant documentation files
- Context is freshest now - capture what future readers need

## Phase 7: Adversarial Review
Think like an attacker, not the author:
- What happens under concurrent execution?
- What if inputs are null, empty, or malformed?
- Are there hardcoded values that should be configurable?
- Does this handle production scale?
- Are there security implications?

Fix anything found before proceeding.

## Phase 8: Quality Gate
- Run full test suite one final time
- Run linter if configured
- Review the complete diff
- Present summary of all changes to user

## Output
- No dedicated output file. Deliverable is working code committed to the project.
- Phase 8 produces a diff summary presented to the user for final approval before closing.
- **CHECKPOINT (Phase 1):** Present the task plan to the user. Do NOT write code until they approve.
- **CHECKPOINT (Phase 8):** Present the complete diff summary. Confirm user is satisfied before marking done.

## When to Skip Phases
- Quick typo fix: Skip to Phase 4
- Pure refactor with existing tests: Skip Phase 3
- Exploratory/prototype: Skip Phases 6-8

State which phases you're skipping and why.
