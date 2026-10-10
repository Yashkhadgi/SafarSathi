import sys
import os
import sqlite3
from datetime import datetime, timezone
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions.db")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def _table_columns(conn, table_name):
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [row["name"] for row in rows]


def _init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    columns = _table_columns(conn, "turns")
    if columns and "created_at" not in columns:
        _migrate_legacy_turns(conn)
    else:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS turns (
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
    conn.commit()


def _migrate_legacy_turns(conn):
    migrated_at = _now()
    conn.execute("ALTER TABLE turns RENAME TO turns_legacy")
    conn.execute("""
        CREATE TABLE turns (
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            turn_index INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    legacy_sessions = conn.execute("""
        SELECT DISTINCT session_id FROM turns_legacy
        WHERE session_id IS NOT NULL AND session_id != ''
    """).fetchall()
    for row in legacy_sessions:
        user_id = f"legacy-{row['session_id']}"
        ensure_user(conn, user_id)
        conn.execute(
            """
            INSERT OR IGNORE INTO sessions (session_id, user_id, title, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (row["session_id"], user_id, "Imported chat", migrated_at),
        )
    conn.execute("""
        INSERT INTO turns (session_id, role, content, turn_index, created_at)
        SELECT session_id, role, content, turn_index, ? FROM turns_legacy
    """, (migrated_at,))


def reset_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DROP TABLE IF EXISTS session_language_preferences")
        conn.execute("DROP TABLE IF EXISTS trusted_contacts")
        conn.execute("DROP TABLE IF EXISTS turns")
        conn.execute("DROP TABLE IF EXISTS turns_legacy")
        conn.execute("DROP TABLE IF EXISTS sessions")
        conn.execute("DROP TABLE IF EXISTS users")
        conn.commit()
        _init_db(conn)
    finally:
        conn.close()


def ensure_user(conn, user_id: str):
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, created_at) VALUES (?, ?)",
        (user_id, _now()),
    )


def create_session(user_id: str, title: str = "New chat") -> str:
    import uuid

    conn = _get_conn()
    try:
        ensure_user(conn, user_id)
        session_id = f"{user_id}:{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO sessions (session_id, user_id, title, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, user_id, title, _now()),
        )
        conn.commit()
        return session_id
    finally:
        conn.close()


def ensure_session(user_id: str, session_id: str = None) -> str:
    import uuid

    conn = _get_conn()
    try:
        ensure_user(conn, user_id)
        if session_id:
            existing = conn.execute(
                "SELECT session_id FROM sessions WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            ).fetchone()
            if existing:
                conn.commit()
                return session_id
        session_id = f"{user_id}:{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO sessions (session_id, user_id, title, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, user_id, "New chat", _now()),
        )
        conn.commit()
        return session_id
    finally:
        conn.close()


def list_user_sessions(user_id: str):
    conn = _get_conn()
    try:
        ensure_user(conn, user_id)
        rows = conn.execute(
            """
            SELECT session_id, title, created_at
            FROM sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()
        return [
            {
                "session_id": row["session_id"],
                "title": row["title"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def update_session_title(session_id: str, title: str):
    title = (title or "New chat").strip()[:60] or "New chat"
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE sessions SET title = ? WHERE session_id = ? AND title = 'New chat'",
            (title, session_id),
        )
        conn.commit()
    finally:
        conn.close()


def save_turn(session_id: str, role: str, content: str):
    conn = _get_conn()
    try:
        cur = conn.cursor()
        existing = cur.execute(
            "SELECT session_id FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not existing:
            user_id = session_id.split(":", 1)[0] if ":" in session_id else f"legacy-{session_id}"
            ensure_user(conn, user_id)
            cur.execute(
                """
                INSERT OR IGNORE INTO sessions (session_id, user_id, title, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, user_id, "New chat", _now()),
            )
        if role == "user":
            title = (content or "New chat").strip()[:60] or "New chat"
            cur.execute(
                "UPDATE sessions SET title = ? WHERE session_id = ? AND title = 'New chat'",
                (title, session_id),
            )
        cur.execute("SELECT COALESCE(MAX(turn_index), -1) + 1 FROM turns WHERE session_id = ?", (session_id,))
        next_index = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO turns (session_id, role, content, turn_index, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, role, content, next_index, _now()),
        )
        conn.commit()
    finally:
        conn.close()


def get_history(session_id: str, max_turns: int = 6):
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT role, content FROM turns WHERE session_id = ? ORDER BY turn_index DESC LIMIT ?",
            (session_id, max_turns),
        )
        rows = cur.fetchall()
        return [(row["role"], row["content"]) for row in reversed(rows)]
    finally:
        conn.close()


def format_history(session_id: str, max_turns: int = 6) -> str:
    history = get_history(session_id, max_turns)
    if not history:
        return ""
    return "\n".join(f"{role}: {content}" for role, content in history)
