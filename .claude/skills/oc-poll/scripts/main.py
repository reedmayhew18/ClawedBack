"""clawed-back FastAPI server — the I/O bridge between web UI and Claude Code."""

import asyncio
import json
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from fastapi.responses import FileResponse

from config import AUTH_TOKEN, HOST, PORT, UPLOADS_DIR, DATA_DIR
import queue_manager
import file_manager

app = FastAPI(title="clawed-back", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Auth middleware ---

def verify_token(request: Request):
    # Allow static files, login page, and auth check without auth
    if request.url.path in ("/", "/login", "/api/auth") or request.url.path.startswith(("/static", "/files/")):
        return
    auth = request.headers.get("Authorization", "")
    if auth == f"Bearer {AUTH_TOKEN}":
        return
    raise HTTPException(status_code=401, detail="Unauthorized")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/api"):
        try:
            verify_token(request)
        except HTTPException as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    return await call_next(request)


# --- API routes ---

@app.post("/api/message")
async def post_message(request: Request):
    """Accept a text message from the user."""
    body = await request.json()
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(400, "Empty message")

    metadata = {}
    if "attachments" in body:
        metadata["attachments"] = body["attachments"]

    queue_manager.write_incoming(content, msg_type="text", metadata=metadata)
    return {"status": "queued"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accept a file upload, save to organized file system, return file_id."""
    content = await file.read()
    original_name = file.filename or "upload"
    result = file_manager.store_bytes(content, original_name, file_type="upload")

    if "error" in result:
        raise HTTPException(500, result["error"])

    # Return file_id (new) and filename (backwards compat for existing chat JS)
    return {
        "file_id": result["file_id"],
        "filename": result["file_id"] + Path(original_name).suffix,
        "original_name": original_name,
        "size": result["size"],
    }


@app.post("/api/voice")
async def upload_voice(file: UploadFile = File(...)):
    """Accept a voice recording, transcribe with whisper, queue the transcription."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"voice_{uuid.uuid4().hex[:8]}.webm"
    dest = UPLOADS_DIR / filename

    content = await file.read()
    dest.write_bytes(content)

    # Transcribe in background to not block
    from voice import transcribe
    result = transcribe(str(dest))

    if "error" in result:
        raise HTTPException(500, f"Transcription failed: {result['error']}")

    # Queue the transcribed text as a message
    queue_manager.write_incoming(
        result["text"],
        msg_type="voice",
        metadata={"audio_file": filename, "language": result.get("language", "unknown")},
    )

    return {"status": "transcribed", "text": result["text"]}


@app.get("/api/events")
async def sse_events(request: Request):
    """SSE stream — pushes new messages (both user and assistant) to the browser."""
    # Track the latest IDs we've already sent so we only push new ones
    conn = queue_manager.get_db()
    row = conn.execute("SELECT COALESCE(MAX(id), 0) as max_id FROM incoming").fetchone()
    last_incoming_id = row["max_id"]
    row = conn.execute("SELECT COALESCE(MAX(id), 0) as max_id FROM outgoing").fetchone()
    last_outgoing_id = row["max_id"]
    row = conn.execute(
        "SELECT COALESCE(MAX(id), 0) as max_id FROM incoming WHERE processed >= 1"
    ).fetchone()
    last_read_id = row["max_id"]
    conn.close()

    async def event_generator():
        nonlocal last_incoming_id, last_outgoing_id, last_read_id
        while True:
            if await request.is_disconnected():
                break

            conn = queue_manager.get_db()

            # Check for new incoming (user) messages
            rows = conn.execute(
                "SELECT * FROM incoming WHERE id > ? ORDER BY id ASC",
                (last_incoming_id,),
            ).fetchall()
            for msg in rows:
                last_incoming_id = msg["id"]
                yield {
                    "event": "user_message",
                    "data": json.dumps({
                        "id": msg["id"],
                        "content": msg["content"],
                        "type": msg["type"],
                        "timestamp": msg["timestamp"],
                        "metadata": json.loads(msg["metadata"] or "{}"),
                    }),
                }

            # Check for new outgoing (assistant) messages
            rows = conn.execute(
                "SELECT * FROM outgoing WHERE id > ? ORDER BY id ASC",
                (last_outgoing_id,),
            ).fetchall()
            for msg in rows:
                last_outgoing_id = msg["id"]
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "id": msg["id"],
                        "content": msg["content"],
                        "type": msg["type"],
                        "timestamp": msg["timestamp"],
                        "metadata": json.loads(msg["metadata"] or "{}"),
                    }),
                }

            # Check for newly read incoming messages
            row = conn.execute(
                "SELECT COALESCE(MAX(id), 0) as max_id FROM incoming WHERE processed >= 1"
            ).fetchone()
            current_read_id = row["max_id"]
            if current_read_id > last_read_id:
                last_read_id = current_read_id
                yield {
                    "event": "read_receipt",
                    "data": json.dumps({"read_up_to": current_read_id}),
                }

            conn.close()
            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())


@app.post("/api/webhook/{name}")
async def webhook(name: str, request: Request):
    """Accept incoming webhooks and queue them for processing."""
    try:
        body = await request.json()
    except Exception:
        body = {"raw": (await request.body()).decode(errors="replace")}

    queue_manager.write_incoming(
        json.dumps(body),
        msg_type="webhook",
        metadata={"webhook_name": name},
    )
    return {"status": "queued"}


@app.get("/api/health")
async def health():
    """Server health check."""
    pending = queue_manager.peek()
    return {
        "status": "ok",
        "pending_messages": pending,
        "timestamp": time.time(),
    }


@app.get("/api/history")
async def get_history():
    """Return recent message history."""
    messages = queue_manager.history(50)
    return {"messages": messages}


@app.post("/api/auth")
async def check_auth(request: Request):
    """Verify a token is valid."""
    body = await request.json()
    if body.get("token") == AUTH_TOKEN:
        return {"valid": True}
    raise HTTPException(401, "Invalid token")


@app.get("/api/shares")
async def get_shares():
    """List active file shares (auth required)."""
    return {"shares": file_manager.list_shares()}


# --- File serving (no auth — share UUID is the secret) ---

@app.get("/files/{share_file}")
async def serve_shared_file(share_file: str, request: Request, filename: str = None):
    """Serve a temporarily shared file by its share UUID."""
    # Parse UUID from filename (e.g., "abc123def456.pdf" -> "abc123def456")
    share_uuid = share_file.rsplit(".", 1)[0] if "." in share_file else share_file

    result = file_manager.resolve_share(share_uuid)
    if result is None:
        raise HTTPException(410, "File share has expired or does not exist.")

    file_path = Path(result["file_path"])
    if not file_path.exists():
        raise HTTPException(404, "File not found on disk.")

    display_name = filename or result.get("original_name", file_path.name)

    return FileResponse(
        path=str(file_path),
        filename=display_name,
        media_type=None,  # FastAPI auto-detects from extension
    )


# --- Static files & SPA fallback ---

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(index_file.read_text())
    return HTMLResponse("<h1>clawed-back</h1><p>Static files not found.</p>")


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="clawed-back server")
    parser.add_argument("--ssl", action="store_true",
                        help="Enable HTTPS (looks for fullchain.pem and privkey.pem in server dir)")
    parser.add_argument("--public", type=str, default=None,
                        help="Path to SSL public certificate (fullchain.pem)")
    parser.add_argument("--private", type=str, default=None,
                        help="Path to SSL private key (privkey.pem)")
    args = parser.parse_args()

    ssl_certfile = None
    ssl_keyfile = None

    if args.ssl or args.public or args.private:
        server_dir = Path(__file__).parent
        certfile = Path(args.public) if args.public else server_dir / "fullchain.pem"
        keyfile = Path(args.private) if args.private else server_dir / "privkey.pem"

        if certfile.exists() and keyfile.exists():
            ssl_certfile = str(certfile)
            ssl_keyfile = str(keyfile)
            proto = "https"
        else:
            print(f"\n  WARNING: SSL requested but certificates not found:")
            if not certfile.exists():
                print(f"    Missing: {certfile}")
            if not keyfile.exists():
                print(f"    Missing: {keyfile}")
            print(f"  Falling back to HTTP.\n")
            proto = "http"
    else:
        proto = "http"

    print(f"\n  clawed-back server starting on {proto}://{HOST}:{PORT}")
    print(f"  Auth token: {AUTH_TOKEN}\n")

    uvicorn.run(app, host=HOST, port=PORT,
                ssl_certfile=ssl_certfile, ssl_keyfile=ssl_keyfile)
