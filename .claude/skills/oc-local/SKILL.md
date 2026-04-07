---
name: oc-local
description: "Run tasks on a local or remote Ollama model instead of Claude. Use when the user says 'run locally', 'use ollama', 'local model', 'process offline', 'use local', '/oc-local', or wants to offload a task to a local LLM."
allowed-tools: "Read Write Edit Bash Grep"
---

# Local Processing via Ollama

Run tasks on a local Ollama model (or a remote Ollama server) for offline/private processing. This is for LOCAL models only — no cloud APIs.

## First Use: Setup

### Check if Ollama is installed locally

```bash
which ollama 2>/dev/null && ollama list 2>/dev/null || echo "OLLAMA_NOT_FOUND"
```

### If Ollama is installed and has models

Show the available models:
```bash
ollama list
```

Present them to the user and ask which one to use as default. Recommend these if available:
- `glm-4.7-flash` — fast, good general use
- `qwen3.5` — strong reasoning
- `gemma4:26b` — excellent quality, moderate speed
- `gemma4:31b` — best quality, slower

### If Ollama is NOT installed or has no models

Ask: **"Ollama isn't available locally. Do you have a remote Ollama server you'd like to connect to?"**

If yes, ask for:
1. Server address (e.g., `192.168.1.100:11434`)
2. Which model to use on that server

If no, tell the user to install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh` and pull a model: `ollama pull gemma4:26b`

### Save the selection

Write the model choice and connection type to `data/sessions/ollama_config.json`:

```json
{
  "mode": "local",
  "model": "gemma4:26b",
  "remote_host": null
}
```

Or for remote:
```json
{
  "mode": "remote",
  "model": "gemma4:26b",
  "remote_host": "192.168.1.100:11434"
}
```

`remote_host` persists even when switching back to local mode — don't null it out. If the user says "switch back to remote" you already have the IP.

This persists until the user specifies a different model or says "use [model] this time" (one-time override).

## Loading Saved Config

On every invocation, check for saved config:
```bash
cat $PROJECT_ROOT/data/sessions/ollama_config.json 2>/dev/null || echo "NO_CONFIG"
```

If no config, run the setup flow above.

If the user specifies a model in their message (e.g., "/oc-local qwen3.5 summarize this file"), use that model for this request only — don't overwrite the saved default.

## Processing Modes

### Mode 1: Single Request (no back-and-forth needed)

For one-shot tasks — summarize, translate, analyze, answer a question, etc.

**Local Ollama:**
```bash
ollama run --model MODEL --keepalive 2m --think true --nowordwrap --yes "FULL_PROMPT_HERE"
```

**Remote Ollama:**
```bash
curl -s http://REMOTE_HOST/api/chat -d '{
  "model": "MODEL",
  "messages": [{"role": "user", "content": "FULL_PROMPT_HERE"}],
  "stream": false
}'
```

Parse the response from `message.content` in the JSON result.

### Mode 2: Agentic Request (multi-step, needs tool use)

For tasks that need Claude Code-style agentic behavior — coding, file manipulation, research with multiple steps, etc.

**Local Ollama:**
```bash
ollama launch claude --model MODEL --keepalive 5m --think true --nowordwrap --yes -- -p "FULL_PROMPT_HERE"
```

**IMPORTANT:** The `-- -p` separator is required — without it, the prompt won't be passed to the Claude Code instance.

**Remote Ollama:** Agentic mode is not supported for remote servers (requires local `ollama launch`). Fall back to Mode 1 with a detailed prompt that breaks the task into explicit steps for the model to follow in a single response.

## Building the Prompt (CRITICAL)

**The local model CANNOT access files, URLs, tools, or conversation history.** You must embed ALL context directly into the prompt text. Never reference a file by path — always inline its contents.

**WRONG:**
```
Fix the bug in server/main.py
```

**RIGHT — use a helper to build the prompt with file contents inlined:**
```bash
python3 -c "
content = open('$PROJECT_ROOT/.claude/skills/oc-poll/scripts/main.py').read()
prompt = f'Fix the bug in the following Python file. The server crashes on startup with a port conflict.\n\n\`\`\`python\n{content}\n\`\`\`'
print(prompt)
" > /tmp/ollama_prompt.txt
```

Then pass the generated prompt:
```bash
ollama run --model MODEL --keepalive 2m --think true --nowordwrap --yes "$(cat /tmp/ollama_prompt.txt)"
```

For remote:
```bash
PROMPT=$(cat /tmp/ollama_prompt.txt)
curl -s http://REMOTE_HOST/api/chat -d "{\"model\": \"MODEL\", \"messages\": [{\"role\": \"user\", \"content\": $(python3 -c "import json; print(json.dumps(open('/tmp/ollama_prompt.txt').read()))")}], \"stream\": false}"
```

### The model is BLIND every time it runs

There is no conversation history between ollama calls. Each invocation starts from zero. If the user says "ok now fix it" after a previous ollama response suggested changes, you MUST include:

1. The original file contents
2. The previous model's analysis/suggestions
3. What the user is now asking

**Example scenario:**

Turn 1 — user asks: "Use the local model to review script.py for performance"
→ You build a prompt with script.py inlined, send to ollama, get back suggestions

Turn 2 — user says: "Ok tell it to fix the script now"
→ The model has NO memory of Turn 1. You must build a NEW prompt that includes:
- The full script.py contents (again)
- The model's previous suggestions from Turn 1
- The instruction to apply those fixes

```python
# Build follow-up prompt with full context
script = open('script.py').read()
previous_analysis = """[paste the model's Turn 1 response here]"""
prompt = f"""You previously analyzed this script and suggested the following improvements:

{previous_analysis}

Now apply ALL of those fixes to the script below and return the complete corrected version.

```python
{script}
```"""
```

**Rules for prompt building:**
- If analyzing a file: read it, inline the full contents
- If following up on a previous ollama response: include BOTH the file AND the previous response
- If working with multiple files: inline all of them with clear headers
- If answering based on conversation context: summarize the relevant context in the prompt
- If coding: include requirements, language, and all relevant code
- Use the Python helper pattern — don't try to manually paste large files into a bash string

## Handling the Response

1. Capture the full output from the local model
2. Present it to the user in the chat via the queue:
```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py write '{"content": "**Local model response (MODEL):**\n\nRESPONSE_HERE", "type": "text"}'
```

If the response is too long for a single queue message, store it as a file and share it:
```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py store /tmp/local_response.md --name "local_response.md" --type generated
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py share FILE_ID --name "local_response.md" --duration 3600
```

## Changing Models

- **"Use gemma4:31b from now on"** → update `ollama_config.json` with new default
- **"Use qwen3.5 for this"** → one-time override, don't change saved config
- **"Switch to remote server 10.0.0.5:11434"** → update config to remote mode
- **"List models"** → run `ollama list` (local) or `curl http://REMOTE_HOST/api/tags` (remote)

## Listing Available Models

**Local:**
```bash
ollama list
```

**Remote:**
```bash
curl -s http://REMOTE_HOST/api/tags | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('models', []):
    print(f\"{m['name']}  ({m.get('size', 'unknown size')})\")
"
```

## Important Rules

1. **Local models only** — this skill is for Ollama (local or self-hosted remote). No cloud APIs.
2. **Include all context in the prompt** — the local model can't see your files or conversation
3. **Don't over-promise** — local models are less capable than Claude. Set expectations.
4. **Respect the user's model choice** — save it, don't second-guess it
5. **For remote mode, always use the API** — don't try to SSH and run ollama commands
6. **Stream: false for remote** — we need the complete response, not streaming chunks
