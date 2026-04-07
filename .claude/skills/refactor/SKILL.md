---
name: refactor
description: Safely refactor code with characterization tests and incremental changes. Use when the user says "refactor", "clean up", "extract", "rename", "restructure", or needs to modernize legacy code.
argument-hint: "[file, module, or description of what to refactor]"
allowed-tools: Read, Edit, Bash, Grep, Glob
---

# Safe Refactoring

## Goal
Improve code structure without changing observable behavior. Success = all tests pass before and after, the diff is reviewable in isolation, and no behavior has been silently altered.

## Dependencies
- Tools: Read, Edit, Bash, Grep, Glob
- Requires a working test runner accessible via Bash (e.g., `pytest`, `jest`, `go test`)
- No external services required

## Context
- Read the target file(s) and any existing tests before planning
- Check CLAUDE.md for project-specific conventions (naming, test locations, build commands)
- Understand the public API / call sites before renaming or extracting

Refactor code incrementally with test coverage as a safety net.

## Process

### Step 1: Characterize Current Behavior
Before changing anything:
1. Read the code to understand what it does
2. Check existing test coverage
3. If coverage is insufficient, write **characterization tests** that capture current behavior:
   - Focus on inputs → outputs for public functions
   - Include edge cases the code currently handles
   - These tests document "what the code does now", not "what it should do"
4. Run tests to confirm they pass

### Step 2: Plan the Refactoring

**CHECKPOINT:** Present the refactoring plan to the user before making any changes. List the steps in order and flag any that touch public APIs, rename exported symbols, or affect many files.
Ask: "Here's the refactoring plan. Anything to adjust before I start?"

Break the refactoring into small, independent steps. Each step should:
- Be completable in one change
- Keep tests passing after the change
- Be easy to review in isolation

Common refactoring sequences:
- **Extract**: Identify code to extract → write test for it → extract → verify
- **Rename**: Find all references → rename → verify no breakage
- **Restructure**: Map dependencies → move in dependency order → verify each move
- **Simplify**: Identify dead code → verify it's unused → remove → verify

### Step 3: Execute Incrementally
For each step:
1. Make the change
2. Run the relevant tests
3. If tests fail: fix or revert before proceeding
4. If tests pass: move to next step

NEVER batch multiple refactoring steps. One logical change at a time.

### Step 4: Verify
After all steps:
1. Run the full test suite
2. Compare behavior: does the refactored code produce identical results?
3. Review the total diff for anything unexpected

## Hard Rules
- NEVER change behavior during refactoring (that's a feature change, not a refactor)
- NEVER skip test verification between steps
- If existing tests are insufficient, write characterization tests FIRST
- Preserve original function signatures as wrappers initially when extracting (remove wrappers in a separate step)
- When renaming across many files, use your editor's rename symbol feature or search-and-replace, not manual edits

**CHECKPOINT:** After all steps are complete and the full test suite passes, present a summary of changes to the user before closing out.
Ask: "Refactoring complete. Here's a summary of what changed. Want me to clean up the characterization tests, or keep them as permanent coverage?"

## Output
- **Primary deliverable:** Refactored source file(s) with all tests passing
- **Secondary deliverable:** Characterization tests (if written) — user decides whether to keep or remove
- **Format:** In-place edits to existing files; no new files unless characterization tests are added
- **Save location:** Same paths as input files
- A brief summary of changes is presented to the user after completion

## Legacy Code Strategy
For large legacy codebases:
1. Spend initial effort on characterization tests (not refactoring)
2. Create module-specific CLAUDE.md files documenting gotchas
3. Use handoff documents (PROGRESS.md) between sessions
4. Target 25-30k tokens per session; use `/clear` between modules
