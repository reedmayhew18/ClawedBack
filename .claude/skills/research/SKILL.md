---
name: research
description: Structured web research with source evaluation and synthesis. Use when the user says "research", "look up", "find out", "what's the best way to", "how do people", "find documentation for", or needs information from the web to make a decision.
argument-hint: "[topic or question]"
allowed-tools: WebSearch, WebFetch, Read, Write, Grep, Glob
---

# Web Research

Systematic web research that produces actionable, cited results - not link dumps.

## Goal

Produce a concise, sourced answer to the user's question that enables a decision or action. Success = direct answer + cited sources + no unanswered gaps. Failure = link dump, unverified claims, or outdated information.

## Dependencies

**Tools:** WebSearch, WebFetch, Read, Write (all declared in frontmatter)
**CLI tools:** None required
**Connectors:** Public web only — no MCP servers or APIs needed

## Context

- No brand voice or codebase conventions needed for general research
- For code-specific research: scan the project's CLAUDE.md or package.json first to understand the tech stack and version constraints before searching
- Reference files in `references/` are not required for this skill

## Process

### Step 1: Understand the Question
Before searching, clarify:
- What specific information do we need?
- What decisions will this inform?
- What would a GOOD answer look like? (docs link? code example? comparison table?)

**CHECKPOINT:** If the question is ambiguous or the scope is unclear, ask one clarifying question before searching. Do NOT proceed with guesses about intent.

### Step 2: Search Strategy
Don't just search once. Use iterative, targeted queries:

**Round 1 - Official sources first:**
- Search for official documentation: `"[tool/library] official docs [topic]"`
- Search for GitHub repos: `"[tool] site:github.com"`
- Search for changelogs/releases if version-specific

**Round 2 - Community knowledge:**
- Stack Overflow / GitHub issues for specific errors or patterns
- Blog posts from known practitioners (not SEO farms)
- Reddit/HN discussions for real-world experience

**Round 3 - Targeted follow-up:**
- Fill gaps from rounds 1-2 with specific queries
- Fetch actual pages (WebFetch) for content that search snippets don't cover

### Step 3: Source Evaluation
Rank sources by reliability:

| Tier | Source Type | Trust Level |
|------|-----------|-------------|
| 1 | Official documentation, RFCs, specs | High - use as primary |
| 2 | Official blog posts, maintainer comments | High - authoritative |
| 3 | Reputable tech blogs (with code examples) | Medium - verify claims |
| 4 | Stack Overflow (high-vote answers) | Medium - check date and version |
| 5 | Random blog posts, tutorials | Low - cross-reference before using |
| 6 | AI-generated content, SEO farms | Ignore - often wrong |

**Red flags to watch for:**
- No dates (could be years outdated)
- No code examples (theory without practice)
- Contradicts official docs
- "Top 10 Best..." listicle format (usually SEO, not substance)
- Content that reads like AI-generated filler

### Step 4: Synthesize
Don't dump links. Produce:

1. **Direct answer** to the question (1-3 paragraphs)
2. **Key findings** with source attribution
3. **Comparison table** if evaluating options
4. **Code examples** from the most reliable source
5. **Caveats** - what's uncertain, version-dependent, or controversial
6. **Sources** - links to the actual pages consulted

### Step 4 (continued): Present findings

**CHECKPOINT:** Present the synthesized findings to the user before saving anything. Ask: "Here's what I found. Should I save this to a file, or is this sufficient?"

### Step 5: Save (if substantial)
For significant research, write findings to a file:
- `RESEARCH.md` for general research
- `RESEARCH-[topic].md` for topic-specific deep dives

This preserves research across context resets.

## Output

- **Primary deliverable:** Inline response with direct answer, key findings, source citations
- **Format:** Markdown — direct answer paragraph, optional comparison table, code examples if relevant, sources list at bottom
- **Save location:** `RESEARCH.md` or `RESEARCH-[topic].md` in the project root (only if the user confirms or the research is substantial enough to warrant persistence)
- **Never save without user confirmation**

## WebFetch Tips
- Fetch documentation pages directly for accurate information
- Fetch GitHub READMEs for library evaluation
- Fetch specific Stack Overflow answers for verified solutions
- If a page is too large, look for the specific section you need
- Some sites block automated fetching - search results may be your best source

## Research Patterns

**"What library should I use?"**
→ Search for comparison posts, check GitHub stars/activity, read official docs for each option, produce comparison table with pros/cons/use-cases

**"How do I do X in framework Y?"**
→ Official docs first (WebFetch the specific docs page), then community examples, produce code example with explanation

**"Why is X happening?"**
→ Search the exact error message, check GitHub issues, read related docs sections, produce root cause + fix

**"What's the current best practice for X?"**
→ Search recent (last 12 months) discussions, check if official stance exists, note if community is divided, present consensus with caveats
