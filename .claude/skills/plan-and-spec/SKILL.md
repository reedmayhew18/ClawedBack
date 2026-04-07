---
name: plan-and-spec
description: Create a structured implementation plan with spec-driven modeling. Use when starting a new feature, complex refactor, or when the user says "plan this", "spec this out", "design this", or "how should we build this". Forces multiple design iterations before coding.
argument-hint: "[feature or task description]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Write
---

# Spec-Driven Planning

## Goal
Produce a written implementation plan (PLAN.md or TECHSPEC.md) that is specific enough for any developer to execute without additional context — including after a session reset or compaction event. Success = a file exists with concrete steps, file paths, success criteria, and documented risks.

## Dependencies
**Tools:** Read, Grep, Glob (discovery), Write (save plan file)
**Context needed:** CLAUDE.md (project conventions), existing code files, any prior PLAN.md or TECHSPEC.md

## Context
Before planning, read:
- `CLAUDE.md` for project conventions, stack, and constraints
- Relevant existing source files at the paths involved
- Any prior plan files to avoid re-solving solved problems

Create a thorough implementation plan that survives context compaction and prevents the "first idea that works" trap.

## Process

### Phase 1: Understand & Clarify
1. Read relevant code, CLAUDE.md, and any existing specs
2. State your assumptions explicitly
3. Ask the user targeted questions about:
   - Technical constraints and requirements
   - Edge cases and failure modes
   - Integration points with existing code
   - Success criteria (what does "done" look like?)
   - Non-functional requirements (performance, security, etc.)

**CHECKPOINT:** Present your assumptions and questions to the user. Do NOT proceed until they respond and validate your understanding.

### Phase 2: Initial Design
Draft a plan covering:
- **Objective**: What we're building and why (1-2 sentences)
- **Approach**: High-level strategy
- **Files to modify/create**: Specific paths
- **Dependencies**: What this touches
- **Testing strategy**: How we verify correctness
- **Risks**: What could go wrong

### Phase 3: Critique the Design
Evaluate your own plan against:
- **Simplicity**: Is there a simpler approach? Are you over-engineering?
- **Testability**: Can each piece be tested independently?
- **Hand-wavy gaps**: Any steps that say "handle edge cases" without specifics?
- **Unverified assumptions**: Did you grep to confirm methods/APIs exist?
- **Failure modes**: What happens when things go wrong?

### Phase 4: Generate Alternative
Address the specific weaknesses from Phase 3:
- If too complex → simpler architecture
- If untestable → different decomposition
- If gaps exist → fill them with specifics

### Phase 5: Iterate
Repeat Phases 3-4 at least twice more. Present the best elements from all iterations.

### Phase 6: Final Plan
Cherry-pick the best elements into a final plan. Present the plan to the user before saving.

**CHECKPOINT:** Ask: "Here's the final plan. Should I save this to PLAN.md, or would you like any changes first?" Do NOT write the file until the user approves.

Write the approved plan to PLAN.md (or TECHSPEC.md if the user prefers) in the project root.

## Output
- **File:** `PLAN.md` or `TECHSPEC.md` in the project root
- **Format:** Markdown using the Plan File Format below
- **Presented to user** before saving for final approval

## Plan File Format

```markdown
# [Feature Name] Plan

## Objective
What we're building and why.

## Success Criteria
- [ ] Specific, testable criterion 1
- [ ] Specific, testable criterion 2

## Approach
High-level strategy.

## Implementation Steps
1. Step with specific file paths and function names
2. Each step is atomic and testable

## Testing Strategy
How each piece gets verified.

## Risks & Mitigations
Known risks and how we handle them.

## Open Questions
Anything unresolved.
```

## Key Principles
- Plans go in files, not just conversation (they survive compaction)
- Grep to verify before assuming methods/APIs exist
- Every step should be atomic enough to implement and test independently
- Include specific file paths and function names, not vague descriptions
- Define success criteria BEFORE implementation to prevent moving goalposts
