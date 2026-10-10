"""Per-turn feedback tied to an owned chat session."""

import re
from datetime import datetime, timezone

from memory import session_memory


REASONS = {"", "wrong_info", "too_long", "language", "other"}


def _connect():
    conn = session_memory._get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            turn_index INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            reason TEXT NOT NULL,
            comment TEXT NOT NULL,
            tools_used TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
        )
    """)
    return conn


def save_feedback(user_id, session_id, pair_index, rating, reason="", comment=""):
    try:
        if reason not in REASONS or rating not in (-1, 1) or len(comment or "") > 500:
            return {"error": "Invalid feedback"}
        with _connect() as conn:
            owner = conn.execute(
                "SELECT user_id FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if not owner or owner["user_id"] != user_id:
                return {"error": "Chat not owned by user"}
            turns = conn.execute(
                "SELECT turn_index, content FROM turns WHERE session_id = ? AND role = 'assistant' "
                "ORDER BY turn_index", (session_id,),
            ).fetchall()
            if not turns:
                return {"error": "No assistant turn to rate"}
            index = int(pair_index) if pair_index is not None else len(turns) - 1
            if not 0 <= index < len(turns):
                return {"error": "Turn not found"}
            turn = turns[index]
            used_match = re.search(r"(?:^|\n)Used:\s*([^\n]+)", turn["content"])
            tools_used = used_match.group(1).strip() if used_match else ""
            conn.execute(
                "INSERT INTO feedback (user_id, session_id, turn_index, rating, reason, "
                "comment, tools_used, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, session_id, turn["turn_index"], rating, reason,
                 (comment or "").strip(), tools_used, datetime.now(timezone.utc).isoformat()),
            )
        return {"saved": True}
    except Exception as exc:
        return {"error": str(exc)}


def feedback_report():
    try:
        with _connect() as conn:
            reasons = conn.execute(
                "SELECT reason, COUNT(*) AS count FROM feedback WHERE rating = -1 "
                "GROUP BY reason ORDER BY count DESC"
            ).fetchall()
            worst = conn.execute(
                "SELECT f.reason, f.comment, f.tools_used, t.content "
                "FROM feedback f JOIN turns t ON t.session_id = f.session_id "
                "AND t.turn_index = f.turn_index WHERE f.rating = -1 "
                "ORDER BY f.created_at DESC LIMIT 20"
            ).fetchall()
        return {"reasons": [dict(row) for row in reasons],
                "worst_answers": [dict(row) for row in worst]}
    except Exception as exc:
        return {"error": str(exc)}
