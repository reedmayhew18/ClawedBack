# OpenClaw → ClawedBack Tool Mapping

A comprehensive guide mapping every OpenClaw tool to its Claude Code equivalent. ClawedBack covers ~19 of 23 OpenClaw tools out of the box — the 4 missing are API wrappers that can be built as skills.

---

## Direct Matches (Identical or Better)

These tools exist in both platforms with equivalent or superior functionality in Claude Code.

| OpenClaw Tool | Claude Code Tool | Notes |
|---|---|---|
| `exec` / `process` | **Bash** | Both run shell commands with foreground/background execution and timeouts. Claude Code adds `run_in_background` for async, and the `sudo` skill for elevated permissions. |
| `read` | **Read** | Both read files. Claude Code also reads images (multimodal), PDFs with page ranges, and Jupyter notebooks natively. **Advantage: Claude Code.** |
| `write` | **Write** | Identical — write file contents to disk. |
| `edit` | **Edit** | Both do targeted edits. Claude Code adds `replace_all` for bulk renames across a file. |
| `apply_patch` | **Edit** (multiple calls) | OpenClaw's patch format handles multi-file hunks in one call. Claude Code uses precise Edit calls per change — more verbose but more accurate (no fuzzy matching failures). |
| `web_search` | **WebSearch** | Both search the web. OpenClaw supports 12 providers (Brave, DuckDuckGo, Exa, etc.). Claude Code's is built-in with no API key required. |
| `web_fetch` | **WebFetch** | Both fetch and process web pages. Claude Code auto-converts HTML→markdown and includes AI-powered summarization. |
| `cron` | **CronCreate** / **CronDelete** / **CronList** | Both manage scheduled jobs with standard 5-field cron expressions. Claude Code jobs are session-scoped with 7-day auto-expiry. |
| `subagents` / `sessions_*` | **Agent** tool | Both spawn isolated sub-agents. Claude Code supports typed agents (Explore, Plan, debugger, researcher, etc.), model selection (opus/sonnet/haiku), git worktree isolation, and background execution. **Advantage: Claude Code** — richer agent type system. |
| `agents_list` | **TaskList** / **TaskGet** | Track and query active agents and tasks. |
| `image` (analyze) | **Read** | Claude is natively multimodal — reading an image file presents it visually for analysis. No separate tool needed. **Advantage: Claude Code** — analysis is built into the base model. |
| — | **Grep** | Claude Code has a dedicated ripgrep-powered search with regex, glob filters, context lines, and multiline support. OpenClaw relies on `exec grep`. **Advantage: Claude Code.** |
| — | **Glob** | Dedicated fast file pattern matching tool. OpenClaw relies on `exec find`. **Advantage: Claude Code.** |

**Score: 13 direct matches.** Claude Code has the edge on several (Read is multimodal, Grep/Glob are dedicated tools, Agent is more typed).

---

## Close Matches (Skill or Wrapper Needed)

These tools have functional equivalents in Claude Code but need a thin skill or Python wrapper.

| OpenClaw Tool | Claude Code Approach | Gap & Fix |
|---|---|---|
| `code_execution` (sandboxed Python) | **Bash** + Python venv | OpenClaw runs Python in a remote xAI sandbox for ephemeral analysis. Claude Code runs Python locally in a venv (`.venv/` at project root). Same result, different isolation model. For true sandboxing, wrap with Docker. |
| `browser` (Chromium automation) | **Bash** + Playwright | OpenClaw has a built-in browser tool (navigate, click, screenshot, JS eval, cookies, viewport emulation). Claude Code achieves the same via Playwright (`pip install playwright`). The toolkit's `webapp-testing` skill already wraps Playwright. For full browser automation, create an `oc-browser` skill. |
| `message` (cross-channel send) | **oc-respond** + **oc-channel** skills | OpenClaw sends messages across 23+ channels natively. ClawedBack sends via SQLite queue → SSE → web UI. As channel adapters are added (Telegram, Discord, etc.), `oc-channel` handles routing. Already architected. |
| `agent send` (CLI dispatch) | **Agent** tool + `claude -p` | OpenClaw's `openclaw agent` runs one agent turn from CLI. Claude Code's `claude -p "prompt"` does the same in headless mode. The `Agent` tool spawns sub-agents within a session. Fully covered. |
| `session_status` | **TaskGet** + session state files | OpenClaw queries session model/status. Our `data/sessions/conversation.json` + `poll_state.json` serve the same purpose. |
| `tts` (text-to-speech) | **Bash** + edge-tts | OpenClaw integrates ElevenLabs, OpenAI, MiniMax, and Microsoft Edge TTS. Claude Code can run `edge-tts` (free, no API key, Microsoft neural voices) or call OpenAI's TTS API. **To build**: `pip install edge-tts` then `edge-tts --text "hello" --write-media output.mp3`. Create an `oc-tts` skill — ~30 lines. |

**Score: 6 close matches.** All achievable with existing tools + a thin wrapper.

---

## Genuinely Missing (No Match)

These tools have no equivalent in Claude Code, even a semi-close one. All are API integrations that could be built as skills.

### `x_search` — X/Twitter Search
- **What it does**: Searches X posts via xAI API. Returns AI-synthesized answers with citations. Supports keyword, semantic, user, and thread searches.
- **Why missing**: Requires xAI API key and their proprietary search endpoint. No built-in Twitter/X search in Claude Code.
- **To build**: Create an `oc-x-search` skill that calls the xAI API via `curl` or `WebFetch`. Needs `XAI_API_KEY`. ~50 lines of skill markdown. Alternatively, use an MCP server that wraps the xAI API.

### `image_generate` — Image Generation
- **What it does**: Generates and edits images via DALL-E, Gemini, Stability AI, etc.
- **Why missing**: Claude Code can analyze images but cannot create them. No built-in image generation.
- **To build**: Create an `oc-image-gen` skill that calls OpenAI's DALL-E API via Python. Needs `OPENAI_API_KEY`. Could also use `/compile-to-skill` on OpenClaw's image generation code to transpile it. ~100 lines including Python script.

### `video_generate` — Video Generation
- **What it does**: Generates videos via APIs (Runway, Pika, etc.).
- **Why missing**: Same as image generation — no built-in creation capability. Very niche.
- **To build**: Create an `oc-video-gen` skill wrapping a video API. Low priority — very few users need this.

### `canvas` — Device Canvas
- **What it does**: Drives presentations and visual content on paired device screens (OpenClaw's macOS/iOS companion app).
- **Why missing**: This is tightly coupled to OpenClaw's native app architecture. There's no equivalent "present content on a remote screen" in Claude Code.
- **To build**: **Skip**. This requires native app integration. Could partially replicate with an HTML artifact skill that opens content in a browser tab via `python -m http.server`, but it's a fundamentally different paradigm.

### `nodes` — Device Pairing
- **What it does**: Discovers and targets paired companion devices (iOS, Android, macOS). Executes commands on remote devices.
- **Why missing**: OpenClaw-specific device pairing protocol with native apps.
- **To build (partial)**: Create an `oc-remote` skill that SSHes into known hosts and runs commands. Covers the "execute on remote device" use case without the native app pairing UX.

### `gateway` — Runtime Management
- **What it does**: Inspects, patches, restarts, and updates the OpenClaw gateway process.
- **Why missing**: This manages OpenClaw's own runtime. Not applicable to Claude Code.
- **To build**: **Skip**. Our equivalents are `oc-setup` (first-run), `oc-resume` (restart after reboot), and `oc-update` (pull upstream updates).

---

## Plugin Tool Equivalents

| OpenClaw Plugin | Claude Code Equivalent | Notes |
|---|---|---|
| **Lobster** (typed workflow runtime) | `wizard` skill | Our 8-phase wizard with built-in verification at each stage. Plus `plan-and-spec` for spec-driven workflows. |
| **LLM Task** (structured JSON output) | Native Claude capability | Claude produces structured JSON when asked. No special tool needed — just say "respond in JSON format." |
| **Diffs** (diff viewing/rendering) | `Bash` + `git diff` | Standard git tooling handles all diff needs. |
| **OpenProse** (markdown workflow orchestration) | `workflow` skill | Our workflow skill does markdown-based pipeline orchestration with state tracking and step dependencies. |

---

## Summary

| Category | Count | Tools |
|---|---|---|
| **Direct match** | 13 | exec, read, write, edit, apply_patch, web_search, web_fetch, cron, subagents, agents_list, image (analyze), grep*, glob* |
| **Close match** | 6 | code_execution, browser, message, agent send, session_status, tts |
| **Missing** | 4 | x_search, image_generate, video_generate, canvas |
| **Not applicable** | 2 | nodes (partial via SSH), gateway (skip) |
| **Plugins** | 4/4 | All covered |

*\* Grep and Glob are Claude Code advantages — dedicated tools where OpenClaw uses `exec`.*

**Bottom line: 19/23 OpenClaw tools have direct or close equivalents. The 4 missing tools are all external API wrappers (X search, image gen, video gen, canvas) that can each be built as a simple skill calling the relevant API.**

---

## ClawedBack Skills With No OpenClaw Equivalent

| ClawedBack Skill | Purpose |
|---|---|
| `oc-files` | Organized file storage (date-based) + temporary share links with expiry |
| `oc-token` | Auth token management (view, regenerate, set custom) |
| `oc-ssl` | Let's Encrypt certificate setup via certbot |
| `oc-update` | Safe upstream updates preserving local config/data |
| `oc-resume` | Self-healing restart (auto-detects setup if config missing) |
| `oc-hub` security scanning | Mandatory 5-category audit of imported skills via isolated subagent |

---

## Building the Missing Tools

For each missing tool, the approach is the same:

1. **Find the OpenClaw source** for that tool's implementation
2. **Run `/compile-to-skill`** to transpile it into a Claude Code skill
3. **Or write from scratch** — these are all thin API wrappers (~50-100 lines each)
4. **Install via `/oc-hub`** once built

The `x_search` and `image_generate` tools are the most useful to build first. `video_generate` and `canvas` are low priority.
