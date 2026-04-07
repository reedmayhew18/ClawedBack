"""clawed-back configuration."""

import os
import secrets
from pathlib import Path

# Paths
# scripts/ is at .claude/skills/oc-poll/scripts/ — 4 parents up to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "messages.db"
UPLOADS_DIR = DATA_DIR / "uploads"  # legacy — new files go to FILES_DIR
FILES_DIR = DATA_DIR / "files"
SESSIONS_DIR = DATA_DIR / "sessions"
LOGS_DIR = DATA_DIR / "logs"

# Server
HOST = os.getenv("OC_HOST", "0.0.0.0")
PORT = int(os.getenv("OC_PORT", "8080"))
HOST_URL = os.getenv("OC_HOST_URL", "")  # e.g., "192.168.1.50", "claude.example.com", "localhost"

# Auth — token stored in a file so it persists across restarts
TOKEN_FILE = DATA_DIR / ".auth_token"


def get_or_create_token() -> str:
    """Return the auth token, generating one on first run."""
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)
    return token


AUTH_TOKEN = get_or_create_token()

# Whisper
WHISPER_MODEL = os.getenv("OC_WHISPER_MODEL", "base.en")
WHISPER_DEVICE = os.getenv("OC_WHISPER_DEVICE", "cpu")  # "cpu", "cuda", or "auto"

# Polling state file (read by oc-poll skill)
POLL_STATE_FILE = SESSIONS_DIR / "poll_state.json"
