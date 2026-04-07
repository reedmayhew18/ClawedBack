---
name: oc-update
description: "Pull the latest ClawedBack updates from GitHub and apply them to the running installation, preserving local config, data, auth tokens, and user-installed skills. Use when the user says 'update', 'upgrade', 'pull latest', 'check for updates', or 'oc-update'."
allowed-tools: "Read Write Edit Bash Glob Grep"
---

# oc-update

Apply upstream ClawedBack updates from GitHub to the running installation, without overwriting local customizations.

## What Is Safe to Update vs. What to Preserve

**Always update (upstream-owned):**
- `server/*.py` — application code
- `.claude/skills/oc-poll/scripts/static/` — web UI files
- `.claude/skills/oc-*/` — core ClawedBack skills (but see conflicts below)
- `.claude/agents/` — agent definitions
- `CLAUDE.md` — project instructions (merge carefully)
- `README.md`, `post_install.md` — docs

**Always preserve (user-owned):**
- `data/` — all runtime data, queue, files, sessions
- `data/.auth_token` — auth token
- `data/clawedback.json` — local config (mode, host_url, port, ssl, etc.)
- `.venv/` — Python virtual environment
- `.claude/skills/oc-poll/scripts/requirements.txt` — only update if upstream changed it, and notify user

**User-installed skills (preserve unless explicitly updating):**
- Any skill in `.claude/skills/` that does NOT exist in the upstream repo — never delete these
- Skills that exist in both upstream and local — show a diff and let the user decide

---

## Step 1: Check for updates

```bash
cd $PROJECT_ROOT
git fetch origin main 2>&1
```

Then check what's changed:
```bash
git log HEAD..origin/main --oneline 2>/dev/null
```

If there are no new commits: tell the user and stop.

If there are new commits: show the list and ask if they want to proceed.

## Step 2: Identify conflicts

Before applying anything, check for local modifications to upstream-managed files:

```bash
git status --short 2>/dev/null
git diff --name-only HEAD origin/main 2>/dev/null
```

Categorize each changed file:
- **Safe to update** — upstream-owned, not locally modified
- **Locally modified** — exists in both local changes and upstream changes → needs review
- **Local-only** — not in upstream (user additions) → preserve always

## Step 3: Stash local modifications to protected files

Before merging, identify and stash anything in `data/` and other preserved paths to avoid conflicts:

```bash
# data/ is gitignored so it won't be touched by git
# But check for any locally modified tracked files that need care
git diff --name-only 2>/dev/null
```

For each locally modified tracked file that is also changed upstream:
- Show the user a diff
- Ask: **"Keep your version / Take upstream / Merge manually?"**

## Step 4: Apply the update

If no conflicts (or conflicts resolved):

```bash
cd $PROJECT_ROOT
git pull origin main 2>&1
```

If git pull fails due to conflicts:
```bash
git stash 2>/dev/null
git pull origin main 2>&1
git stash pop 2>/dev/null
```

Show the merge result.

## Step 5: Post-update checks

After pulling:

**Check if requirements changed:**
```bash
git diff HEAD~1 HEAD -- .claude/skills/oc-poll/scripts/requirements.txt 2>/dev/null
```

If requirements changed, install the new deps:
- Mode A/B: `source $PROJECT_ROOT/.venv/bin/activate && pip install -r $PROJECT_ROOT/.claude/skills/oc-poll/scripts/requirements.txt`
- Mode C: `pip install --break-system-packages -r $PROJECT_ROOT/.claude/skills/oc-poll/scripts/requirements.txt`

Read the mode from `data/clawedback.json`:
```bash
python3 -c "import json; c=json.load(open('$PROJECT_ROOT/data/clawedback.json')); print(c.get('mode','c'))"
```

**Check if server needs restart:**
```bash
git diff HEAD~1 HEAD --name-only 2>/dev/null | grep "oc-poll/scripts/"
```

If any `server/` files changed, restart the server:
```bash
pkill -f "python3 main.py" 2>/dev/null || true
sleep 2
```

Then restart using the saved config:
```bash
python3 -c "
import json
c = json.load(open('$PROJECT_ROOT/data/clawedback.json'))
print(c.get('server_cmd','cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python3 main.py'))
"
```

Run the server command with nohup in the background.

Verify:
```bash
sleep 3
curl -sk http://localhost:${OC_PORT:-8080}/ -o /dev/null -w "%{http_code}"
```

## Step 6: Preserve local skill additions

After the pull, check if git removed any user-installed skills (shouldn't happen, but verify):

```bash
ls $PROJECT_ROOT/.claude/skills/
```

If any user-added skills are missing, restore them from git stash or warn the user.

## Step 7: Report

```
Update complete!

Commits applied: N
  - abc1234  Add feature X
  - def5678  Fix bug Y

Files updated:
  .claude/skills/oc-poll/scripts/main.py
  server/config.py
  .claude/skills/oc-poll/SKILL.md

Preserved (unchanged):
  data/clawedback.json
  data/.auth_token

Server: restarted (new server files detected)
Requirements: unchanged

Your local additions (untouched):
  .claude/skills/my-custom-skill/
```

If the server was restarted, remind: "You'll need to re-enter your auth token if your browser session expired."

---

## Error Recovery

If `git pull` fails and leaves the repo in a broken state:

```bash
git merge --abort 2>/dev/null || true
git reset --hard HEAD
```

Then tell the user what happened and suggest:
```
git fetch origin main
git reset --hard origin/main
```

**Warning**: `git reset --hard` will discard local changes to tracked files. `data/` is safe (gitignored). Always warn before running this.

---

## Notes

- This skill only updates the ClawedBack codebase — it does NOT update Claude Code itself.
- If the user has made edits directly to core skill files (like `oc-hub/SKILL.md`), those edits will conflict. The skill will show the diff and let them choose.
- The skill preserves `data/clawedback.json` so all config (port, host_url, mode, SSL) survives the update.
