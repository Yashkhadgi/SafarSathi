import sys
import os
import sqlite3
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS turns (
            session_id TEXT,
            role TEXT,
            content TEXT,
            turn_index INTEGER
        )
    """)
    return conn


def save_turn(session_id: str, role: str, content: str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(turn_index), -1) + 1 FROM turns WHERE session_id = ?", (session_id,))
    next_index = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO turns (session_id, role, content, turn_index) VALUES (?, ?, ?, ?)",
        (session_id, role, content, next_index),
    )
    conn.commit()
    conn.close()


def get_history(session_id: str, max_turns: int = 6):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content FROM turns WHERE session_id = ? ORDER BY turn_index DESC LIMIT ?",
        (session_id, max_turns),
    )
    rows = cur.fetchall()
    conn.close()
    return list(reversed(rows))


def format_history(session_id: str, max_turns: int = 6) -> str:
    history = get_history(session_id, max_turns)
    if not history:
        return ""
    return "\n".join(f"{role}: {content}" for role, content in history)
