---
name: oc-tools
description: "Execute tools and commands on behalf of the user from the web chat. Use internally when the router identifies a tool request. Do NOT invoke directly."
user-invocable: false
allowed-tools: "Read Write Edit Bash Grep Glob WebFetch WebSearch"
---

# Tool Executor

Executes tools and commands requested by the user through the web chat.

## Available Capabilities

You have full Claude Code tool access. Here's what you can do for the user:

### File Operations
- **Read files** — any file on the system
- **Write/edit files** — within the project directory (outside requires approval)
- **Search files** — glob patterns and content search

### Shell Commands
- **Run commands** — execute bash commands (dangerous ones need approval)
- **Python scripts** — run Python code
- **System info** — check disk, processes, environment

### Web
- **Search** — web search for information
- **Fetch** — retrieve web pages and APIs

### Code
- **Write code** — generate, modify, debug code
- **Analyze** — review code, find bugs, suggest improvements
- **Refactor** — restructure code safely

## Execution Rules

1. **Check approval first** — if the operation is destructive or modifies files outside `$PROJECT_ROOT/`, request approval via oc-approve before executing
2. **Show your work** — include relevant output in your response so the user sees what happened
3. **Handle errors gracefully** — if a command fails, explain why and suggest alternatives
4. **Stay scoped** — only do what the user asked. Don't add bonus features or clean up code they didn't mention
5. **Report results** — always respond with what you did and the outcome

## Response Pattern

After executing a tool:

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py write '{"content": "Done. Here is what I found:\n\n...", "type": "text"}'
```
