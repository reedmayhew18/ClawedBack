---
name: tdd
description: Test-driven development workflow. Use when implementing features or fixing bugs where the user says "TDD", "test first", "write tests", or wants a red-green-refactor cycle.
argument-hint: "[feature or bug description]"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Test-Driven Development

## Goal

Implement a feature or bug fix using strict red-green-refactor discipline. Success = all tests pass, no regressions, and the implementation is covered by mutation-resistant assertions.

## Dependencies

- **Tools:** Read, Write, Edit, Bash, Grep, Glob
- **CLI:** Project's test runner (e.g., `pytest`, `jest`, `go test`, `npm test`)

## Context

- Read existing test files to understand naming conventions and test framework in use
- Check CLAUDE.md or project docs for test file locations and runner commands
- Identify the test framework before writing any tests

## Process

### Step 1: Understand the Requirement
- Read relevant code and existing tests
- Identify the behavior being added or fixed
- Determine test file location following project conventions

### Step 2: Write Failing Tests (RED)
Write tests FIRST that:
- Cover the happy path
- Cover edge cases (null inputs, empty collections, boundary values)
- Cover error conditions
- Use **mutation-resistant assertions**: assert specific values, not truthiness
  - Good: `assertEqual(result.status, 'completed')`
  - Bad: `assertTrue(result)` or `assertNotNone(result)`

Run the tests. They MUST fail. If they pass, the tests aren't testing new behavior.

**CHECKPOINT:** Show the failing tests to the user. Do NOT proceed until they confirm the tests correctly capture the intended behavior. Ask: "Here are the failing tests. Do these cover what you need, or should I add/change anything before implementing?"

### Step 3: Commit the Tests
Stage and note the failing tests. This prevents accidentally modifying tests to make them pass.

### Step 4: Implement Minimum Code (GREEN)
Write the minimum code to make ALL tests pass:
- No extra features
- No premature abstractions
- No "while I'm here" improvements
- Just make the tests green

Run the full test suite (not just new tests) to catch regressions.

### Step 5: Refactor (REFACTOR)
Only after tests pass:
- Extract common patterns
- Improve naming
- Remove duplication
- Simplify logic

Run tests after each refactor step. Tests must stay green.

### Step 6: Verify
- Run the complete test suite one final time
- Confirm no regressions
- Review the diff for anything unexpected

**CHECKPOINT:** Present the final diff and test output to the user before finishing. Ask: "All tests pass. Here's the final diff. Does this look correct, or anything to adjust?"

## Output

- **Deliverable:** Updated source file(s) + test file(s), all tests passing
- **Format:** Code files in their existing project locations; no new files unless required by the feature
- **Test results:** Show final test runner output confirming green suite
- **Logged changes:** Available via `git diff` for user review

## Testing Guidelines

**Assertion Quality:**
```
# BAD - passes with garbage data
assert result is not None
assert len(items) > 0

# GOOD - catches real bugs
assertEqual(result.user_id, 'usr_123')
assertEqual(len(items), 3)
assertEqual(items[0].name, 'Expected Name')
```

**Test Independence:**
- Each test sets up its own state
- No test depends on another test's side effects
- Tests can run in any order

**What to Test:**
- Public API behavior, not implementation details
- State changes, not method calls
- Output correctness, not internal structure
