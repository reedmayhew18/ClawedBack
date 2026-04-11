import sys
import argparse

def _read_lines(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            return f.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


def _detect_newline(lines):
    for line in lines:
        if line.endswith('\r\n'):
            return '\r\n'
        if line.endswith('\n'):
            return '\n'
    return '\n'


def edit_file(file_path, start_line, end_line, new_content):
    lines = _read_lines(file_path)

    # Python lists are 0-indexed, so start_line 1 is index 0
    start_idx = start_line - 1
    end_idx = end_line

    # start_idx > end_idx (i.e., start_line > end_line + 1) is invalid.
    # start_idx == end_idx (i.e., end_line == start_line - 1) is a pure insertion
    # with no replacement — enables inserting into an empty file (1, 0),
    # appending after the last line (len+1, len), or inserting before line N (N, N-1).
    if start_idx < 0 or end_idx > len(lines) or start_idx > end_idx:
        print(f"Error: Invalid line range {start_line}-{end_line} for file with {len(lines)} lines.")
        sys.exit(1)

    # Detect the file's dominant line ending so inserted content matches.
    file_newline = _detect_newline(lines)

    # Normalize new_content to the file's line ending.
    if file_newline == '\r\n':
        new_content = new_content.replace('\r\n', '\n').replace('\n', '\r\n')

    # Prepare new content. Ensure each line ends with a newline.
    # If the user provides a single string without a trailing newline, we add it.
    if new_content and not new_content.endswith('\n'):
        new_content += file_newline

    new_lines_to_insert = new_content.splitlines(keepends=True)

    # If the content was empty or just newlines, splitlines might behave differently
    if not new_lines_to_insert and new_content == "":
         new_lines_to_insert = []
    elif not new_lines_to_insert and new_content == "\n":
         new_lines_to_insert = ["\n"]

    # Perform replacement
    updated_lines = lines[:start_idx] + new_lines_to_insert + lines[end_idx:]

    try:
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.writelines(updated_lines)
        print(f"Successfully replaced lines {start_line}-{end_line} in {file_path}")
    except Exception as e:
        print(f"Error writing file: {e}")
        sys.exit(1)


def read_range(file_path, start_line, end_line):
    lines = _read_lines(file_path)

    start_idx = start_line - 1
    end_idx = end_line

    # For read, start must be <= end and both within the file.
    if start_idx < 0 or end_idx > len(lines) or start_idx >= end_idx:
        print(f"Error: Invalid line range {start_line}-{end_line} for file with {len(lines)} lines.")
        sys.exit(1)

    # Print with 1-indexed line numbers (cat -n style) so the caller can see
    # exactly which line numbers to target for a subsequent edit.
    width = len(str(end_line))
    for i in range(start_idx, end_idx):
        content = lines[i].rstrip('\r\n')
        print(f"{str(i + 1).rjust(width)}\t{content}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Robustly read or edit a file by line range.")
    parser.add_argument("file_path", help="Path to the file")
    parser.add_argument("start_line", type=int, help="The first line (1-indexed)")
    parser.add_argument("end_line", type=int, help="The last line (inclusive, 1-indexed). For editing, may be start_line - 1 to insert without replacing.")
    parser.add_argument("new_content", nargs="?", default=None, help="The new content to insert (editing mode; omit if using --stdin or --read)")
    parser.add_argument("--stdin", action="store_true", help="Read new content from stdin instead of the new_content argument (recommended for multi-line content to avoid shell escaping issues)")
    parser.add_argument("--read", action="store_true", help="Read and print lines start_line..end_line (inclusive) with line numbers, instead of editing")

    args = parser.parse_args()

    if args.read:
        read_range(args.file_path, args.start_line, args.end_line)
        sys.exit(0)

    if args.stdin:
        new_content = sys.stdin.read()
    elif args.new_content is not None:
        new_content = args.new_content
    else:
        parser.error("new_content is required unless --stdin or --read is used")

    edit_file(args.file_path, args.start_line, args.end_line, new_content)
