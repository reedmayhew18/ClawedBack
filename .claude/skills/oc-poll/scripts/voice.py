"""Whisper transcription wrapper for clawed-back.

Usage:
    python voice.py <audio_file>

Returns JSON: {"text": "transcribed text", "language": "en"}

Reads OC_WHISPER_MODEL and OC_WHISPER_DEVICE from environment/config.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ALLOWED_MODELS = frozenset({
    "tiny", "tiny.en", "base", "base.en", "small", "small.en",
    "medium", "medium.en", "large", "large-v1", "large-v2", "large-v3",
    "turbo",
})
ALLOWED_DEVICES = frozenset({"cpu", "cuda", "auto"})
UPLOADS_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "uploads"


def transcribe(audio_path: str, model: str = None, device: str = None) -> dict:
    """Transcribe an audio file using whisper CLI."""
    audio = Path(audio_path).resolve()

    # Validate the file exists
    if not audio.exists():
        return {"error": f"File not found: {audio_path}"}

    # Path traversal check — file must be inside data/uploads/
    uploads = UPLOADS_DIR.resolve()
    if not str(audio).startswith(str(uploads)):
        return {"error": "Audio file must be in data/uploads/"}

    # Validate model against allowlist
    model = model or os.getenv("OC_WHISPER_MODEL", "base.en")
    if model not in ALLOWED_MODELS:
        return {"error": f"Invalid model: {model}"}

    # Validate device against allowlist
    device = device or os.getenv("OC_WHISPER_DEVICE", "cpu")
    if device not in ALLOWED_DEVICES:
        return {"error": f"Invalid device: {device}"}

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            "whisper",
            str(audio),
            "--model", model,
            "--output_format", "json",
            "--output_dir", tmpdir,
        ]

        if device != "auto":
            cmd.extend(["--device", device])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            return {"error": result.stderr.strip()[:500]}

        # Whisper writes <filename>.json
        json_files = list(Path(tmpdir).glob("*.json"))
        if not json_files:
            return {"error": "No transcription output"}

        with open(json_files[0]) as f:
            data = json.load(f)

        return {
            "text": data.get("text", "").strip(),
            "language": data.get("language", "unknown"),
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python voice.py <audio_file>", file=sys.stderr)
        sys.exit(1)

    result = transcribe(sys.argv[1])
    print(json.dumps(result))


if __name__ == "__main__":
    main()
