---
name: oc-files
description: "Manage files and create temporary share links for the web chat. Use when the user says 'share file', 'send file', 'list files', 'download', or when you need to provide a file to the user via the chat. Also use when you generate a file (PDF, image, code, etc.) and want to let the user download it."
allowed-tools: "Bash(python*) Read Write"
---

# File Manager

Store, organize, and share files with the user via temporary download links.

## Sharing a File with the User

When you create or have a file the user should be able to download, use the share command:

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py share <file_id> --name "Report.pdf" --duration 3600
```

This returns a JSON with a `url` field. Send that URL as a markdown link in your response:

```
[Report.pdf](http://localhost:8080/files/abc123def456.pdf?filename=Report.pdf)
```

The user clicks it and downloads the file. The link expires after the duration (default: 60 minutes, max: 7 days).

## Storing a New File

If you generated a file (wrote it to disk), store it in the organized file system first:

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py store /path/to/file.pdf --name "Report.pdf" --type generated
```

Then share it:
```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py share <file_id> --name "Report.pdf"
```

Types: `upload` (user uploaded), `voice` (voice recording), `generated` (you created it), `output` (command output).

## Commands

```bash
# List all stored files
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py list

# List files from a specific date
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py list --date 2026-04-05

# Get the disk path for a file ID
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py get <file_id>

# Share a file (default 60 min)
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py share <file_id> --name "File.pdf" --duration 3600

# Share for longer (e.g., 24 hours)
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py share <file_id> --duration 86400

# Revoke a share early
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py unshare <share_uuid>

# List active shares
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py shares

# Clean up expired shares
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py cleanup
```

## Workflow: User Asks for a File

1. Create/find the file on disk
2. `file_manager.py store <path> --name "name.ext" --type generated` → get `file_id`
3. `file_manager.py share <file_id> --name "name.ext"` → get `url`
4. Send in chat: `[name.ext](url)`

## Workflow: Reading a User's Uploaded File

User uploads come through with a `file_id` in the message metadata. To read:

```bash
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts && python file_manager.py get <file_id>
```

This prints the absolute path — then use the Read tool on that path.

## Duration Limits

- Minimum: 60 seconds
- Default: 3600 seconds (1 hour)
- Maximum: 604800 seconds (7 days)

## File Organization

Files are stored in `data/files/YYYY/MM/DD/<file_id>.<ext>`. The manifest at `data/files/manifest.json` tracks all files with metadata. Shares are tracked in `data/files/shared_files.json` with expiry timestamps.
