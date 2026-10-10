"""Per-user message window and estimated daily token budget."""

import math
import sqlite3
import time
from datetime import datetime, timezone

from memory import session_memory


MESSAGE_LIMIT = 30
WINDOW_SECONDS = 600
DAILY_TOKEN_LIMIT = 50000


def _connect():
    conn = session_memory._get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usage_events (
            user_id TEXT NOT NULL,
            created_at REAL NOT NULL,
            token_estimate INTEGER NOT NULL,
            kind TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    return conn


def _today_start():
    now = datetime.now(timezone.utc)
    return datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp()


def check_and_record_message(user_id, message):
    try:
        tokens = max(1, math.ceil(len(message or "") / 4))
        now = time.time()
        with _connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            count = conn.execute(
                "SELECT COUNT(*) FROM usage_events WHERE user_id = ? AND kind = 'message' "
                "AND created_at > ?", (user_id, now - WINDOW_SECONDS),
            ).fetchone()[0]
            total = conn.execute(
                "SELECT COALESCE(SUM(token_estimate), 0) FROM usage_events "
                "WHERE user_id = ? AND created_at >= ?", (user_id, _today_start()),
            ).fetchone()[0]
            if count >= MESSAGE_LIMIT:
                return {"error": "Aapne 10 minute ki message limit chhoo li. Thoda ruko aur phir try karo."}
            if total + tokens > DAILY_TOKEN_LIMIT:
                return {"error": "Aaj ki token limit poori ho gayi. Kal phir try karo."}
            session_memory.ensure_user(conn, user_id)
            conn.execute("INSERT INTO usage_events VALUES (?, ?, ?, 'message')",
                         (user_id, now, tokens))
        return {"allowed": True}
    except sqlite3.Error as exc:
        return {"error": str(exc)}


def record_reply(user_id, reply):
    try:
        tokens = max(1, math.ceil(len(reply or "") / 4))
        with _connect() as conn:
            conn.execute("INSERT INTO usage_events VALUES (?, ?, ?, 'reply')",
                         (user_id, time.time(), tokens))
        return {"recorded": True}
    except sqlite3.Error as exc:
        return {"error": str(exc)}


def usage_today(user_id):
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FILTER (WHERE kind = 'message'), "
                "COALESCE(SUM(token_estimate), 0) FROM usage_events "
                "WHERE user_id = ? AND created_at >= ?",
                (user_id, _today_start()),
            ).fetchone()
        return {"calls_today": row[0], "approx_tokens_today": row[1],
                "daily_token_cap": DAILY_TOKEN_LIMIT}
    except sqlite3.Error:
        return {"calls_today": 0, "approx_tokens_today": 0,
                "daily_token_cap": DAILY_TOKEN_LIMIT}
