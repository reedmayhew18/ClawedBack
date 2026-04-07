"""Organized file system and temporary file sharing for clawed-back.

CLI:
    python file_manager.py store <filepath> [--name original.pdf] [--type upload|voice|generated]
    python file_manager.py get <file_id>
    python file_manager.py share <file_id> [--name Filename.pdf] [--duration 3600]
    python file_manager.py unshare <share_uuid>
    python file_manager.py cleanup
    python file_manager.py list [--date 2026-04-05]
"""

import argparse
import json
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

FILES_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "files"
MANIFEST_PATH = FILES_DIR / "manifest.json"
SHARES_PATH = FILES_DIR / "shared_files.json"

MAX_SHARE_DURATION = 7 * 24 * 3600  # 7 days
DEFAULT_SHARE_DURATION = 3600  # 60 minutes

ALLOWED_TYPES = frozenset({"upload", "voice", "generated", "output"})


def _load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    return {"files": {}}


def _save_manifest(data: dict):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _load_shares() -> dict:
    if SHARES_PATH.exists():
        with open(SHARES_PATH) as f:
            return json.load(f)
    return {"shares": {}}


def _save_shares(data: dict):
    SHARES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SHARES_PATH, "w") as f:
        json.dump(data, f, indent=2)


def store(filepath: str, original_name: str = None, file_type: str = "upload") -> dict:
    """Store a file in the organized date-based directory structure."""
    src = Path(filepath)
    if not src.exists():
        return {"error": f"File not found: {filepath}"}

    if file_type not in ALLOWED_TYPES:
        return {"error": f"Invalid type: {file_type}. Must be one of: {', '.join(ALLOWED_TYPES)}"}

    original_name = original_name or src.name
    ext = Path(original_name).suffix
    file_id = uuid.uuid4().hex[:12]

    now = datetime.now(timezone.utc)
    date_dir = FILES_DIR / now.strftime("%Y/%m/%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    dest_name = f"{file_id}{ext}"
    dest = date_dir / dest_name
    shutil.copy2(str(src), str(dest))

    rel_path = dest.relative_to(FILES_DIR)

    manifest = _load_manifest()
    manifest["files"][file_id] = {
        "original_name": original_name,
        "path": str(rel_path),
        "type": file_type,
        "stored_at": now.isoformat(),
        "size": dest.stat().st_size,
    }
    _save_manifest(manifest)

    return {
        "file_id": file_id,
        "path": str(rel_path),
        "original_name": original_name,
        "stored_at": now.isoformat(),
        "size": dest.stat().st_size,
    }


def store_bytes(content: bytes, original_name: str, file_type: str = "upload") -> dict:
    """Store raw bytes directly (used by the upload endpoint)."""
    if file_type not in ALLOWED_TYPES:
        return {"error": f"Invalid type: {file_type}"}

    ext = Path(original_name).suffix
    file_id = uuid.uuid4().hex[:12]

    now = datetime.now(timezone.utc)
    date_dir = FILES_DIR / now.strftime("%Y/%m/%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    dest_name = f"{file_id}{ext}"
    dest = date_dir / dest_name
    dest.write_bytes(content)

    rel_path = dest.relative_to(FILES_DIR)

    manifest = _load_manifest()
    manifest["files"][file_id] = {
        "original_name": original_name,
        "path": str(rel_path),
        "type": file_type,
        "stored_at": now.isoformat(),
        "size": len(content),
    }
    _save_manifest(manifest)

    return {
        "file_id": file_id,
        "path": str(rel_path),
        "original_name": original_name,
        "stored_at": now.isoformat(),
        "size": len(content),
    }


def get(file_id: str) -> Path | None:
    """Resolve a file_id to its absolute path. Returns None if not found."""
    manifest = _load_manifest()
    entry = manifest["files"].get(file_id)
    if not entry:
        return None
    full = FILES_DIR / entry["path"]
    if full.exists():
        return full
    return None


def get_info(file_id: str) -> dict | None:
    """Get metadata for a file_id."""
    manifest = _load_manifest()
    return manifest["files"].get(file_id)


def share(file_id: str, original_name: str = None, duration_seconds: int = DEFAULT_SHARE_DURATION) -> dict:
    """Create a temporary share link for a file."""
    manifest = _load_manifest()
    entry = manifest["files"].get(file_id)
    if not entry:
        return {"error": f"File not found: {file_id}"}

    full_path = FILES_DIR / entry["path"]
    if not full_path.exists():
        return {"error": f"File missing from disk: {entry['path']}"}

    duration_seconds = min(max(int(duration_seconds), 60), MAX_SHARE_DURATION)

    original_name = original_name or entry["original_name"]
    ext = Path(original_name).suffix or Path(entry["path"]).suffix

    share_uuid = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    expires_at = datetime.fromtimestamp(now.timestamp() + duration_seconds, tz=timezone.utc)

    shares = _load_shares()
    shares["shares"][share_uuid] = {
        "file_id": file_id,
        "original_name": original_name,
        "extension": ext,
        "shared_at": now.isoformat(),
        "duration_seconds": duration_seconds,
        "expires_at": expires_at.isoformat(),
    }
    _save_shares(shares)

    port = os.getenv("OC_PORT", "8080")
    host_url = os.getenv("OC_HOST_URL", "")

    # Try reading from config if env var not set
    if not host_url:
        config_path = FILES_DIR.parent / "clawedback.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                host_url = config.get("host_url", "")
            except (json.JSONDecodeError, KeyError):
                pass

    # Fallback to localhost
    if not host_url:
        host_url = "localhost"

    # If host_url is already a full URL, use it as the base directly
    if host_url.startswith(("http://", "https://")):
        url = f"{host_url.rstrip('/')}/files/{share_uuid}{ext}?filename={original_name}"
    else:
        protocol = "https" if os.getenv("OC_SSL", "") == "1" else "http"
        config_path = FILES_DIR.parent / "clawedback.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                if config.get("ssl", {}).get("enabled"):
                    protocol = "https"
            except (json.JSONDecodeError, KeyError):
                pass
        url = f"{protocol}://{host_url}:{port}/files/{share_uuid}{ext}?filename={original_name}"

    return {
        "share_uuid": share_uuid,
        "url": url,
        "original_name": original_name,
        "expires_at": expires_at.isoformat(),
        "duration_seconds": duration_seconds,
    }


def unshare(share_uuid: str) -> dict:
    """Revoke a file share."""
    shares = _load_shares()
    if share_uuid not in shares["shares"]:
        return {"error": f"Share not found: {share_uuid}"}
    del shares["shares"][share_uuid]
    _save_shares(shares)
    return {"status": "removed"}


def resolve_share(share_uuid: str) -> dict | None:
    """Look up a share by UUID. Returns share info + file path if valid, None if not found or expired."""
    shares = _load_shares()

    # Strip extension from UUID if present
    share_uuid = share_uuid.split(".")[0] if "." in share_uuid else share_uuid

    entry = shares["shares"].get(share_uuid)
    if not entry:
        return None

    expires_at = datetime.fromisoformat(entry["expires_at"])
    now = datetime.now(timezone.utc)
    if now > expires_at:
        # Expired — clean it up
        del shares["shares"][share_uuid]
        _save_shares(shares)
        return None

    file_path = get(entry["file_id"])
    if not file_path:
        return None

    return {
        **entry,
        "file_path": str(file_path),
    }


def cleanup_expired() -> dict:
    """Remove all expired shares."""
    shares = _load_shares()
    now = datetime.now(timezone.utc)
    expired = []
    for sid, entry in list(shares["shares"].items()):
        expires_at = datetime.fromisoformat(entry["expires_at"])
        if now > expires_at:
            expired.append(sid)
            del shares["shares"][sid]
    _save_shares(shares)
    return {"removed": len(expired), "ids": expired}


def list_files(date_filter: str = None) -> list:
    """List files, optionally filtered by date (YYYY-MM-DD)."""
    manifest = _load_manifest()
    results = []
    for fid, entry in manifest["files"].items():
        if date_filter:
            stored = entry.get("stored_at", "")
            if not stored.startswith(date_filter):
                continue
        results.append({"file_id": fid, **entry})
    return sorted(results, key=lambda x: x.get("stored_at", ""), reverse=True)


def list_shares() -> list:
    """List all active (non-expired) shares."""
    shares = _load_shares()
    now = datetime.now(timezone.utc)
    results = []
    for sid, entry in shares["shares"].items():
        expires_at = datetime.fromisoformat(entry["expires_at"])
        if now <= expires_at:
            results.append({"share_uuid": sid, **entry})
    return results


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="clawed-back file manager")
    sub = parser.add_subparsers(dest="command")

    p_store = sub.add_parser("store", help="Store a file")
    p_store.add_argument("filepath")
    p_store.add_argument("--name", default=None, help="Original filename")
    p_store.add_argument("--type", default="upload", choices=sorted(ALLOWED_TYPES))

    p_get = sub.add_parser("get", help="Get file path by ID")
    p_get.add_argument("file_id")

    p_share = sub.add_parser("share", help="Create a share link")
    p_share.add_argument("file_id")
    p_share.add_argument("--name", default=None, help="Display filename")
    p_share.add_argument("--duration", type=int, default=DEFAULT_SHARE_DURATION, help="Seconds (default 3600)")

    p_unshare = sub.add_parser("unshare", help="Revoke a share")
    p_unshare.add_argument("share_uuid")

    sub.add_parser("cleanup", help="Remove expired shares")

    p_list = sub.add_parser("list", help="List files")
    p_list.add_argument("--date", default=None, help="Filter by date (YYYY-MM-DD)")

    sub.add_parser("shares", help="List active shares")

    args = parser.parse_args()

    if args.command == "store":
        result = store(args.filepath, original_name=args.name, file_type=args.type)
        print(json.dumps(result, indent=2))

    elif args.command == "get":
        path = get(args.file_id)
        if path:
            print(str(path))
        else:
            print(json.dumps({"error": "not found"}))
            sys.exit(1)

    elif args.command == "share":
        result = share(args.file_id, original_name=args.name, duration_seconds=args.duration)
        print(json.dumps(result, indent=2))

    elif args.command == "unshare":
        result = unshare(args.share_uuid)
        print(json.dumps(result))

    elif args.command == "cleanup":
        result = cleanup_expired()
        print(json.dumps(result))

    elif args.command == "list":
        results = list_files(date_filter=args.date)
        print(json.dumps(results, indent=2))

    elif args.command == "shares":
        results = list_shares()
        print(json.dumps(results, indent=2))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
