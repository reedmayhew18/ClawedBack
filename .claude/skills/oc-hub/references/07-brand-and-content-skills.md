# Brand and Content Skills in Claude Code

A practical guide to content automation patterns using Claude Code. While the examples are brand and marketing focused, the underlying patterns — shared context folders, progressive disclosure, ICP calibration, and the Grill Me skill — apply to any domain where Claude needs rich project-specific context to produce non-generic output.

---

## 1. Brand Voice Architecture

### The Core Problem

Without explicit context, Claude produces generic output. The same skill prompt that writes good content for one project will write mediocre, interchangeable content for another. Solving this requires giving Claude structured access to your project's identity documents.

### The Tone of Voice Profile

A Tone of Voice profile is a reference document that instructs Claude on the personality and style constraints for all generated content. Store it in your shared context folder (not inline in CLAUDE.md) and reference it from individual skill files.

A complete Tone of Voice profile includes:

- **Personality traits**: High-level tone descriptors. Example: "Write like you're talking to one person over coffee, not presenting to a boardroom."
- **Banned words and phrases**: Specific vocabulary Claude must never use. This prevents AI-sounding artifacts and enforces brand conventions.
- **Platform-specific rules**: Formatting or stylistic rules per publishing channel (LinkedIn vs. email vs. ad copy).
- **Voice examples**: Actual past content — best-performing posts, emails, copy — that Claude can model against.

### Banned Vocabulary and AI Artifact Elimination

A banned words list is one of the highest-leverage inputs you can give a content skill. Categories to include:

- **AI-generated text markers**: Punctuation and phrasing that signals AI authorship. Em dashes (—) are a well-known example; their overuse is a common AI tell.
- **Off-brand jargon**: Terminology that contradicts the persona. A Gen Z fintech app bans "synergistic wealth accumulation" and replaces it with "Let's grow your stash."
- **Overly technical terms**: If content targets business buyers rather than engineers, ban terms like "existing stacks," "CLI tool," or "full IDE."
- **Unapproved brand names or forms**: Enforce abbreviations. Ban "anti-gravity," require "AG."

**Enforcement via hooks**: Including banned words in a reference file is good. Enforcing them mechanically is better. Claude Code hooks are deterministic scripts that run automatically after Claude writes output. A post-write hook can scan every draft against your banned words list without consuming AI reasoning tokens, providing a reliable backstop that never forgets.

---

## 2. Content Pillars

### What Content Pillars Are

Content pillars are a short, enumerated list of the core topics and themes a project covers. They constrain what the AI writes *about*, the same way a Tone of Voice profile constrains *how* it writes.

Example (boutique travel agency):
> "All blog and social content must fall into one of four pillars: 1. Hidden Gem Destinations, 2. Luxury Packing Guides, 3. Sustainable Tourism Practices, 4. Local Cuisine Spotlights."

### Why They Matter for AI Skills

When a content skill (SEO optimizer, blog writer, social media drafter) reads content pillars before generating output, it:

- Produces content scoped to the right topics rather than whatever seems plausible
- Ensures SEO-targeted content attracts traffic with the correct commercial intent
- Eliminates the need to re-specify focus on every individual request

### Where to Store Them

Content pillars belong in the shared context folder (see Section 5), not duplicated inside every skill's references directory. A single source of truth means every new skill you add inherits the pillars automatically.

---

## 3. Ideal Customer Profiles

### Structure of an ICP Document

An Ideal Customer Profile (ICP) tells Claude who it is writing *for*. It replaces vague instructions like "write for business owners" with a specific, citable profile Claude can reason against.

A complete ICP includes:

| Field | Example |
|---|---|
| Persona name | Master Plumber Mike |
| Demographics | 40–55 years old |
| Behaviors / responsibilities | Runs a 5–15 person plumbing crew |
| Pain points | Struggles with paper-based scheduling and dispatch |
| Values | Prefers saving time over learning complex tech |
| Core goal | Reduce missed appointments, track technician locations |

Pain points and values are the highest-signal fields. Pain points describe the specific friction the customer experiences. Values describe what tradeoffs they favor when choosing a solution. Together, they give Claude the reasoning it needs to write copy that addresses *why* this person would care — not just *who* they are.

### ICP as a Calibration Document

Treat the ICP as a calibration input, not boilerplate. The more specific the pain points and values, the more Claude's output will diverge from generic AI writing. An ICP with real behavioral specifics ("struggles with paper-based scheduling and dispatch") produces meaningfully different output than a vague one ("values efficiency").

### Multiple ICPs

Projects with multiple audiences can maintain separate ICP files — one per persona — and reference the appropriate one from each skill's context needs chart.

---

## 4. Progressive Disclosure for Content

### The Core Pattern

Progressive disclosure is how Claude Code structures skills to protect the context window. Instead of loading everything at once, skills are designed as a three-tier hierarchy:

**Tier 1 — YAML Front Matter (always loaded)**
The metadata at the top of every `skill.md`: name, description, trigger words. Always present in context. Hard limit: 15,000 characters total across all skill descriptions in a project.

**Tier 2 — skill.md body (loaded on activation)**
The step-by-step SOP for the task. Loaded only when Claude activates the skill. Should stay under 200 lines. Acts as a table of contents pointing to Tier 3 resources.

**Tier 3 — references/ folder (loaded on demand)**
Everything else: brand guidelines, ICP documents, positioning statements, voice examples, templates, scripts, assets. Claude loads a specific file when it reaches the step that requires it, then can release it before loading the next.

### Why 200 Lines

200 lines is the empirically recommended maximum for `skill.md` body content. It is the length at which an LLM can efficiently scan a document, understand the skill's scope, and decide which reference files to load — without the scanning itself becoming a token drain.

### Refactoring Bloated Skills

If you have an existing skill (downloaded from a marketplace or accumulated over time) that exceeds this, use the skill creator skill to refactor it automatically:

```
Use the skill creator skill to refactor it. I want the skill.md to be max 200 lines
and we want to put all of the reference info inside the references folder.
```

The skill creator will extract heavy text into targeted reference files and rewrite the `skill.md` as a lean table of contents. A 400-line file becoming 148 lines (60% reduction) with four new reference files is a representative outcome. It can also improve the YAML front matter to make activation more reliable.

### Context Needs Chart

Inside `skill.md`, a context needs chart is an explicit instruction block that maps each skill step to its required reference file. Example:

```
Step 3 — Audience alignment:
  Read: references/icp-primary.md
  Purpose: Know who this content is for

Step 4 — Competitive framing:
  Read: ../shared-brand-context/positioning.md
  Purpose: Differentiate from competitors correctly
```

This pattern makes progressive disclosure explicit and auditable rather than implicit.

---

## 5. Shared Context Folders

### The Problem With Per-Skill Context

If every skill duplicates the ICP, positioning statement, and tone of voice profile inside its own `references/` folder, you now have multiple copies of the same documents. Updating your brand voice means editing every skill individually.

### The Shared Brand Context Folder

Create a single centralized folder — `shared-brand-context/` or similar — at the workspace level. Populate it with the project's identity documents:

```
shared-brand-context/
  icp-primary.md          # Main audience persona
  icp-secondary.md        # Secondary persona (if applicable)
  positioning.md          # Competitive differentiation summary
  tone-of-voice.md        # Voice profile + banned words
  content-pillars.md      # Core topic list
  case-studies/           # Reference examples and templates
```

Individual skills then reference these files by path rather than duplicating their content. A new skill added to the project inherits all context immediately.

### Market Positioning Document

The positioning document deserves specific attention. Its job is to give Claude "citation-worthy framing" — the specific differentiators it can use when writing competitive content.

Effective structure:
> "Unlike [competitor type] that [negative behavior], we offer [specific differentiator] that [concrete benefit]."

Example:
> "Unlike massive coffee conglomerates that rely on single-use plastic pods and obscure supply chains, we offer 100% compostable packaging and transparent, direct-trade sourcing that pays farmers 20% above fair-trade minimums."

The direct contrast structure forces specificity and gives Claude language it can actually use rather than abstractions it has to interpret.

---

## 6. Practical Skill Patterns

### Building a Context-Aware Content Skill

1. **Identify the skill type**: SEO optimizer, email drafter, social post writer, etc.
2. **Generate the base structure**: Use the skill creator skill to produce a lean `skill.md` with a `references/` directory.
3. **Populate references**: Move ICP, tone of voice, positioning, and content pillars into either the skill's `references/` folder or the shared context folder.
4. **Write the context needs chart**: In `skill.md`, map each relevant step to its reference file.
5. **Test against a real task**: The output should sound like your brand, not generic AI.

### The Grill Me Skill

The Grill Me skill is a three-sentence prompt that forces Claude to conduct a thorough interview before producing any plan, content, or code:

> "Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree resolving dependencies between decisions one by one. And finally, if a question can be answered by exploring the codebase, explore the codebase instead."

**Why it works**: It is based on the concept of a "design tree" (from Frederick P. Brooks' *The Design of Design*). Every design decision has downstream dependencies. Choosing an advanced search feature means you must then resolve the filters, sorting methods, pagination behavior, and so on. The Grill Me skill forces resolution of this tree *before* any output is committed.

**Applied to content work**: When starting a new content system, campaign, or brand voice, running Grill Me before writing any skill or reference document surfaces all the dependencies you would otherwise discover mid-execution:
- Who is the primary audience vs. secondary?
- What topics are in scope vs. out of scope for each pillar?
- Which banned words apply everywhere vs. only to specific channels?
- What does success look like — traffic, conversions, engagement?

**The questions are dynamic**: Claude generates questions based on the specific context you provide. A complex brand architecture might produce 30–50 questions. A simple blog skill might produce 10. The "16 questions" number associated with the skill comes from a specific demonstration (Matt Pocock's split-pane editor feature design), not a fixed question set.

**Grill Me as a discovery tool**: Using Grill Me at the start of any project involving Claude — content or otherwise — produces a shared understanding document that can itself be stored in the shared context folder. Every subsequent skill then has access to the reasoning that shaped the architecture.

### Integrating Context Into an Existing Skill

If you have a working skill that produces generic output, you do not need to rebuild it. The upgrade path:

1. Create or locate your shared context folder with ICP, positioning, and tone of voice documents.
2. Add a context needs chart section to the existing `skill.md`.
3. Point the relevant steps at the appropriate reference files.
4. Run the skill creator skill to refactor if the file has grown beyond 200 lines.

The skill's outputs will shift from generic to project-specific without changing its core logic.

---

## Summary: The Content Automation Stack

| Layer | What it is | Where it lives |
|---|---|---|
| Brand voice | Tone, banned words, voice examples | `shared-brand-context/tone-of-voice.md` |
| ICP | Audience persona with pain points and values | `shared-brand-context/icp-*.md` |
| Positioning | Competitive differentiation statement | `shared-brand-context/positioning.md` |
| Content pillars | Core topic scope | `shared-brand-context/content-pillars.md` |
| Skill SOP | Step-by-step task instructions | `skill.md` (≤200 lines) |
| Context needs chart | Maps steps to reference files | Inside `skill.md` |
| Hooks | Deterministic post-write enforcement | Background scripts |
| Grill Me | Pre-flight shared understanding | Applied before architecture decisions |

The pattern scales to any project that needs Claude to produce non-generic, contextually calibrated output: content, code review, documentation, customer communications, or anything else with a defined audience and style.
