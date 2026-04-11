---
name: robust-edit
description: "Robust, line-based file editing. Replace a range of lines in a file with new content by line number instead of exact string matching. Use when the user says 'robust-edit', '/robust-edit', 'replace lines', 'edit lines N to M', or when character-level matching with the Edit tool keeps failing on multi-line changes or uncertain whitespace."
allowed-tools: "Read Bash"
---

# robust-edit

Line-based file editing that sidesteps the exact-string-matching failures smaller models often hit with the standard `Edit` tool. You give it a line range and the new content; it replaces those lines verbatim.

## When to use this

- Multi-line refactors where the exact surrounding whitespace is uncertain.
- The `Edit` tool keeps failing on `old_string` not being unique or not matching.
- You already know the line numbers of the block you want to replace.
- You want to delete a line range (pass empty new content).
- You want to insert content without replacing anything (into an empty file, before a specific line, or at the end of a file).

For single-character tweaks or simple unique-string replacements, the regular `Edit` tool is still simpler — use this skill when line-based editing is actually the right fit.

## How to use

This skill is driven by a helper script at `scripts/robust_edit.py` in this skill directory. The agent invokes it from Bash after reading (or re-reading) the file to determine line numbers.

### Step 1 — Locate line numbers

Use either of these to find the 1-indexed line numbers of the block you want to edit:

- The `Read` tool on the target file (line numbers come from the `cat -n` prefix).
- The script's own `--read` mode (see "Reading a range" below) — useful if you only want a narrow slice of a large file without pulling the whole thing through the Read tool.

### Step 2 — Invoke the helper script

**Preferred form — `--stdin` (multi-line content):**

```bash
python3 /absolute/path/to/.claude/skills/robust-edit/scripts/robust_edit.py \
  <file_path> <start_line> <end_line> --stdin <<'EOF'
<new content goes here>
can span as many lines as you want
EOF
```

Using `--stdin` with a quoted heredoc (`'EOF'`) is the safest way to pass multi-line content: Bash does no expansion, so `$variables`, backticks, backslashes, and special characters all pass through literally. This is the recommended form.

**Alternate form — content as an argv argument (short/single-line content):**

```bash
python3 /absolute/path/to/.claude/skills/robust-edit/scripts/robust_edit.py \
  <file_path> <start_line> <end_line> "<new_content>"
```

**Arguments:**

| Arg | Description |
|---|---|
| `file_path` | Absolute path to the file to edit. |
| `start_line` | 1-indexed first line to replace. |
| `end_line` | 1-indexed last line to replace (inclusive). |
| `new_content` | Replacement text. Omit when using `--stdin`. Pass an empty string `""` to delete the range. |
| `--stdin` | Read `new_content` from stdin instead of argv. |

**Important — passing multi-line content via argv:**

If you use the argv form (not `--stdin`), do **not** use a plain `"..."` string with literal `\n` — Bash will pass the backslash-n through as two characters, not as a real newline, and the script will write the literal `\n` into the file. Use ANSI-C quoting instead:

```bash
python3 scripts/robust_edit.py index.html 10 15 $'<header>\n    <h1>New Title</h1>\n</header>'
```

When in doubt, prefer `--stdin`.

**Deleting a line range:**
```bash
python3 scripts/robust_edit.py index.html 10 15 ""
```

**Inserting without replacing anything** — pass `end_line = start_line - 1`. The new content is inserted before `start_line` and nothing is removed:

```bash
# Insert before line 5 (does not touch line 5 or later)
python3 scripts/robust_edit.py file.py 5 4 --stdin <<'EOF'
new line A
new line B
EOF

# Insert into an empty file
python3 scripts/robust_edit.py empty.py 1 0 --stdin <<'EOF'
first line
EOF

# Append after the last line (if file has N lines, use start=N+1, end=N)
python3 scripts/robust_edit.py file.py 11 10 --stdin <<'EOF'
appended line
EOF
```

### Reading a range

To print a specific range of lines with their line numbers (without editing):

```bash
python3 scripts/robust_edit.py <file_path> <start_line> <end_line> --read
```

Output format is `<lineno>\t<content>`, one line per row, so you can see exactly which line numbers to target for a subsequent edit. `end_line` must be `>= start_line` and within the file (no insertion-style ranges for read mode).

```bash
$ python3 scripts/robust_edit.py example.py 10 13 --read
10	def greet(name):
11	    print(f"Hello, {name}")
12	
13	greet("world")
```

### Step 3 — Verify

Use `Read` again on the file to confirm the replacement landed correctly. Always verify before moving on — line-based edits are unforgiving if you miscounted.

## Example

Replace lines 10 through 15 of `index.html` with a new header block:

```bash
python3 /home/user/project/.claude/skills/robust-edit/scripts/robust_edit.py \
  /home/user/project/index.html 10 15 --stdin <<'EOF'
<header>
    <h1 class="modern-title">New Title</h1>
</header>
EOF
```

Output on success:
```
Successfully replaced lines 10-15 in /home/user/project/index.html
```

## Notes

- The script preserves the rest of the file byte-for-byte — only the specified line range changes.
- Files are read and written as UTF-8.
- Line endings are auto-detected from the existing file (LF or CRLF). Inserted content is normalized to match, so you can pass plain `\n` from Bash even on a CRLF file.
- If `new_content` does not end with a newline, one is added so the file's line structure stays consistent.
- The script exits non-zero with a clear message on any error (bad range, unreadable file, unwritable file).
