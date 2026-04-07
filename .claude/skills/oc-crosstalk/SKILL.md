---
name: oc-crosstalk
description: "Communicate with another ClawedBack instance. Use when the user says 'crosstalk', 'talk to server', 'contact instance', 'send message to', or '/oc-crosstalk'. Enables ClawedBack-to-ClawedBack communication."
allowed-tools: "Bash(curl*) Bash(python*) Read Write"
---

# CrossTalk — ClawedBack Instance Communication

Send messages to and receive responses from another ClawedBack instance. This enables two ClawedBack installations to communicate directly.

## Usage

```
/oc-crosstalk <server_ip_or_url> <auth_token> <message>
```

**Arguments from `$ARGUMENTS`:**
- First argument: server IP or URL (e.g., `192.168.1.50:8080` or `https://chat.example.com`)
- Second argument: auth token for the remote instance
- Remaining arguments: the message/reason for reaching out

**Example:**
```
/oc-crosstalk 192.168.1.50:8080 abc123token Hey, can you check if the deploy finished on your end?
```

## Step 1: Parse Arguments

Extract from `$ARGUMENTS`:
- `REMOTE_HOST` — first word (IP:port or URL)
- `REMOTE_TOKEN` — second word
- `MESSAGE` — everything after the second word

If the host doesn't include a protocol, prepend `http://`.
If the host doesn't include a port, append `:8080`.

## Step 2: Send the Message

```bash
curl -s -X POST "$REMOTE_HOST/api/message" \
  -H "Authorization: Bearer $REMOTE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"content\": \"[CrossTalk from $(hostname)]: $MESSAGE\"}"
```

The message is prefixed with `[CrossTalk from <hostname>]` so the remote instance knows it came from another ClawedBack, not a human typing in the web UI.

Tell the user: "Message sent to $REMOTE_HOST. Waiting for response..."

## Step 3: Wait for Response

Don't use a bash loop with inline Python — it causes permission prompt issues. Instead, use **separate sequential commands**:

1. First, save the current message count:
```bash
curl -s "$REMOTE_HOST/api/history" -H "Authorization: Bearer $REMOTE_TOKEN" -o /tmp/crosstalk_before.json
```

2. Use a **sandwich polling pattern**: quick check first (20s), then longer waits (55s) between retries. This catches fast responses without wasting time, but doesn't hammer the server.

Each poll cycle is two separate Bash calls (no loops — avoids permission prompt issues):

**First check (quick — 20s):**
```bash
sleep 20 && curl -s "$REMOTE_HOST/api/history" -H "Authorization: Bearer $REMOTE_TOKEN" -o /tmp/crosstalk_check.json
```

**Compare:**
```bash
python3 -c "
import json
before = json.load(open('/tmp/crosstalk_before.json'))
after = json.load(open('/tmp/crosstalk_check.json'))
if len(after['messages']) > len(before['messages']):
    last = [m for m in after['messages'] if m['role'] == 'assistant'][-1]
    print(last['content'])
else:
    print('WAITING')
"
```

If WAITING, do subsequent checks with 55s sleep:
```bash
sleep 55 && curl -s "$REMOTE_HOST/api/history" -H "Authorization: Bearer $REMOTE_TOKEN" -o /tmp/crosstalk_check.json
```

Then compare again (same python command as above).

3. Repeat the 55s sleep + check cycle up to 4 more times (total ~5 minutes: 20s + 55s + 55s + 55s + 55s). Once you get a response that isn't WAITING, proceed to Step 4.

4. If no response after 5 minutes, tell the user: "No response received from $REMOTE_HOST after 5 minutes. The remote instance may be offline or busy."

## Step 4: Report the Response

Send the remote instance's reply back to the user via the local queue:

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python queue_manager.py write "{\"content\": \"**Response from $REMOTE_HOST:**\n\n$RESULT\", \"type\": \"text\"}"
```

## File Sharing Between Instances

File sharing is **disabled by default**. Only share files if the user explicitly says to in their message (e.g., "send them the report" or "share the log file with them").

When file sharing is enabled by the user:

1. Use `file_manager.py share` to create a temporary link with a **60-second expiry**:
```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py share <file_id> --name "filename.ext" --duration 60
```

2. Include the link in the message to the remote instance:
```bash
curl -s -X POST "$REMOTE_HOST/api/message" \
  -H "Authorization: Bearer $REMOTE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"content\": \"[CrossTalk from $(hostname)]: Here's the file: [filename.ext]($SHARE_URL)\"}"
```

The 60-second window is intentional — just long enough for the remote instance to download it, short enough to minimize exposure.

## Important Rules

1. **Always prefix messages** with `[CrossTalk from <hostname>]` so the remote instance can identify the source
2. **Never send auth tokens, API keys, or sensitive data** in crosstalk messages unless the user explicitly instructs it
3. **File sharing is off by default** — only enabled when the user's message explicitly requests it
4. **File share links expire in 60 seconds** — keep them short-lived
5. **Don't loop indefinitely** — 5 minute timeout on waiting for responses
6. **Report failures clearly** — if the remote instance is unreachable, say so immediately
7. **This is human-initiated** — a user on this end asked to contact the remote instance. The remote instance sees it as a user message in their chat.

---

*CrossTalk is designed for quick, short-term, human-initiated exchanges between Claude Code / ClawedBack instances. It is not designed or intended for long-term or automated use. All usage of this skill is subject to [Anthropic's Terms of Service](https://www.anthropic.com/legal/consumer-terms).*
