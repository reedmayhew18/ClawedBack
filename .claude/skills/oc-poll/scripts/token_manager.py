"""Auth token management for clawed-back.

CLI:
    python token_manager.py show          — display the current token
    python token_manager.py regenerate    — generate a new random token
    python token_manager.py set <token>   — set a custom token
"""

import secrets
import sys
from pathlib import Path

TOKEN_FILE = Path(__file__).parent.parent.parent.parent.parent / "data" / ".auth_token"


def show() -> str:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return "(no token set — start the server to generate one)"


def regenerate() -> str:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)
    return token


def set_token(token: str) -> str:
    if len(token) < 8:
        print("Error: token must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)
    return token


def main():
    if len(sys.argv) < 2:
        print("Usage: python token_manager.py <show|regenerate|set <token>>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "show":
        print(show())

    elif cmd == "regenerate":
        token = regenerate()
        print(f"New token: {token}")
        print("Restart the server for the new token to take effect.")

    elif cmd == "set":
        if len(sys.argv) < 3:
            print("Usage: python token_manager.py set <token>", file=sys.stderr)
            sys.exit(1)
        token = set_token(sys.argv[2])
        print(f"Token set. Restart the server for it to take effect.")

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
