"""SQLite message queue for clawed-back.

CLI interface for Claude Code skills to interact with the queue:
    python queue_manager.py peek              — count of unprocessed incoming messages
    python queue_manager.py read              — read oldest unprocessed message (marks as processing)
    python queue_manager.py write '<json>'    — write a response to the outgoing queue
    python queue_manager.py ack <id>          — mark incoming message as processed
    python queue_manager.py history <n>       — last N messages (both directions) for context
    python queue_manager.py activity          — timestamp of last user message (for hybrid polling)
"""

import json
import sqlite3
import sys
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "messages.db"


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS incoming (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            type TEXT NOT NULL DEFAULT 'text',
            content TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            processed INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS outgoing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            type TEXT NOT NULL DEFAULT 'text',
            content TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            delivered INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_incoming_unprocessed
            ON incoming(processed, timestamp);
        CREATE INDEX IF NOT EXISTS idx_outgoing_undelivered
            ON outgoing(delivered, timestamp);
    """)


# --- Queue operations ---

def peek() -> int:
    """Return count of unprocessed incoming messages."""
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM incoming WHERE processed = 0"
    ).fetchone()
    conn.close()
    return row["cnt"]


def read():
    """Read the oldest unprocessed message and mark it as processing (processed=1)."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM incoming WHERE processed = 0 ORDER BY timestamp ASC LIMIT 1"
    ).fetchone()
    if row is None:
        conn.close()
        return None
    conn.execute("UPDATE incoming SET processed = 1 WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()
    return dict(row)


def write_response(data: dict):
    """Write a response to the outgoing queue."""
    conn = get_db()
    conn.execute(
        "INSERT INTO outgoing (timestamp, type, content, metadata) VALUES (?, ?, ?, ?)",
        (
            time.time(),
            data.get("type", "text"),
            data.get("content", ""),
            json.dumps(data.get("metadata", {})),
        ),
    )
    conn.commit()
    conn.close()


def write_incoming(content: str, msg_type: str = "text", metadata: dict = None):
    """Write a user message to the incoming queue."""
    conn = get_db()
    conn.execute(
        "INSERT INTO incoming (timestamp, type, content, metadata) VALUES (?, ?, ?, ?)",
        (time.time(), msg_type, content, json.dumps(metadata or {})),
    )
    conn.commit()
    conn.close()


def ack(msg_id: int):
    """Mark an incoming message as fully processed (processed=2)."""
    conn = get_db()
    conn.execute("UPDATE incoming SET processed = 2 WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()


def history(n: int = 20) -> list:
    """Return the last N messages from both queues, interleaved by timestamp."""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, 'user' as role, timestamp, type, content, metadata, processed FROM incoming
        UNION ALL
        SELECT id, 'assistant' as role, timestamp, type, content, metadata, 0 as processed FROM outgoing
        ORDER BY timestamp DESC
        LIMIT ?
    """, (n,)).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def last_activity() -> float:
    """Return the timestamp of the most recent incoming message, or 0."""
    conn = get_db()
    row = conn.execute(
        "SELECT MAX(timestamp) as ts FROM incoming"
    ).fetchone()
    conn.close()
    return row["ts"] or 0.0


def get_undelivered() -> list:
    """Return all undelivered outgoing messages and mark them delivered."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM outgoing WHERE delivered = 0 ORDER BY timestamp ASC"
    ).fetchall()
    if rows:
        ids = [r["id"] for r in rows]
        conn.execute(
            f"UPDATE outgoing SET delivered = 1 WHERE id IN ({','.join('?' * len(ids))})",
            ids,
        )
        conn.commit()
    conn.close()
    return [dict(r) for r in rows]


# --- CLI ---

def main():
    if len(sys.argv) < 2:
        print("Usage: python queue_manager.py <peek|read|write|ack|history|activity>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "peek":
        count = peek()
        print(json.dumps({"pending": count}))

    elif cmd == "read":
        msg = read()
        if msg is None:
            print(json.dumps({"message": None}))
        else:
            print(json.dumps(msg, default=str))

    elif cmd == "write":
        if len(sys.argv) < 3:
            print("Usage: python queue_manager.py write '<json>'", file=sys.stderr)
            sys.exit(1)
        data = json.loads(sys.argv[2])
        write_response(data)
        print(json.dumps({"status": "ok"}))

    elif cmd == "ack":
        if len(sys.argv) < 3:
            print("Usage: python queue_manager.py ack <id>", file=sys.stderr)
            sys.exit(1)
        ack(int(sys.argv[2]))
        print(json.dumps({"status": "ok"}))

    elif cmd == "history":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        msgs = history(n)
        print(json.dumps(msgs, default=str))

    elif cmd == "activity":
        ts = last_activity()
        print(json.dumps({"last_activity": ts}))

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
