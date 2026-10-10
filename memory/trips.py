"""Session-owned trip storage and immutable trip versions."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from memory import session_memory


def _now():
    return datetime.now(timezone.utc).isoformat()


def _connect():
    conn = sqlite3.connect(session_memory.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            trip_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            data_json TEXT NOT NULL,
            current_version INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trip_versions (
            trip_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            data_json TEXT NOT NULL,
            change_summary TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (trip_id, version),
            FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE CASCADE
        )
    """)
    return conn


def save_new_trip(session_id, data, title=None):
    """Return a persisted trip or an error without raising."""
    try:
        with _connect() as conn:
            owner = conn.execute(
                "SELECT user_id FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if owner is None:
                return {"error": "Session not found"}
            trip_id = uuid.uuid4().hex
            now = _now()
            data = dict(data, trip_id=trip_id, version=1)
            payload = json.dumps(data, ensure_ascii=False)
            conn.execute(
                "INSERT INTO trips VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (trip_id, session_id, owner["user_id"],
                 (title or data.get("destination") or "Trip")[:100], payload, 1, now, now),
            )
            conn.execute(
                "INSERT INTO trip_versions VALUES (?, ?, ?, ?, ?)",
                (trip_id, 1, payload, "Initial plan", now),
            )
            return data
    except Exception as exc:
        return {"error": str(exc)}


def get_trip(trip_id, session_id=None, user_id=None):
    try:
        if not session_id and not user_id:
            return {"error": "Owner required"}
        with _connect() as conn:
            scope = "session_id = ?" if session_id else "user_id = ?"
            row = conn.execute(
                f"SELECT data_json FROM trips WHERE trip_id = ? AND {scope}",
                (trip_id, session_id or user_id),
            ).fetchone()
            return json.loads(row["data_json"]) if row else {"error": "Trip not found"}
    except Exception as exc:
        return {"error": str(exc)}


def latest_trip(session_id):
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT data_json FROM trips WHERE session_id = ? ORDER BY updated_at DESC LIMIT 1",
                (session_id,),
            ).fetchone()
            return json.loads(row["data_json"]) if row else {"error": "No trip in this chat"}
    except Exception as exc:
        return {"error": str(exc)}


def save_version(trip_id, session_id, data, change_summary):
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT current_version FROM trips WHERE trip_id = ? AND session_id = ?",
                (trip_id, session_id),
            ).fetchone()
            if row is None:
                return {"error": "Trip not found in this chat"}
            version = row["current_version"] + 1
            data = dict(data, trip_id=trip_id, version=version)
            payload = json.dumps(data, ensure_ascii=False)
            now = _now()
            conn.execute(
                "UPDATE trips SET data_json = ?, current_version = ?, updated_at = ? "
                "WHERE trip_id = ? AND session_id = ?",
                (payload, version, now, trip_id, session_id),
            )
            conn.execute(
                "INSERT INTO trip_versions VALUES (?, ?, ?, ?, ?)",
                (trip_id, version, payload, change_summary, now),
            )
            return data
    except Exception as exc:
        return {"error": str(exc)}


def undo_trip(trip_id, session_id):
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT current_version FROM trips WHERE trip_id = ? AND session_id = ?",
                (trip_id, session_id),
            ).fetchone()
            if row is None:
                return {"error": "Trip not found in this chat"}
            if row["current_version"] <= 1:
                return {"error": "No previous version"}
            previous = conn.execute(
                "SELECT data_json FROM trip_versions WHERE trip_id = ? AND version = ?",
                (trip_id, row["current_version"] - 1),
            ).fetchone()
            restored = json.loads(previous["data_json"])
        return save_version(trip_id, session_id, restored, "Undo previous edit")
    except Exception as exc:
        return {"error": str(exc)}


def list_trips(user_id):
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT trip_id, session_id, title, current_version, data_json, updated_at "
                "FROM trips WHERE user_id = ? ORDER BY updated_at DESC", (user_id,),
            ).fetchall()
            return [{"trip_id": row["trip_id"], "session_id": row["session_id"],
                     "title": row["title"], "version": row["current_version"],
                     "data": json.loads(row["data_json"]), "updated_at": row["updated_at"]}
                    for row in rows]
    except Exception:
        return []


def rename_trip(trip_id, user_id, title):
    try:
        title = str(title or "").strip()[:100]
        if not title:
            return {"error": "Enter a trip title"}
        with _connect() as conn:
            cursor = conn.execute("UPDATE trips SET title = ?, updated_at = ? "
                                  "WHERE trip_id = ? AND user_id = ?",
                                  (title, _now(), trip_id, user_id))
        return {"renamed": cursor.rowcount > 0} if cursor.rowcount else {"error": "Trip not found"}
    except Exception as exc:
        return {"error": str(exc)}


def delete_trip(trip_id, user_id):
    try:
        with _connect() as conn:
            owned = conn.execute("SELECT trip_id FROM trips WHERE trip_id = ? AND user_id = ?",
                                 (trip_id, user_id)).fetchone()
            if not owned:
                return {"error": "Trip not found"}
            conn.execute("DELETE FROM trip_versions WHERE trip_id = ?", (trip_id,))
            conn.execute("DELETE FROM trips WHERE trip_id = ? AND user_id = ?", (trip_id, user_id))
        return {"deleted": True}
    except Exception as exc:
        return {"error": str(exc)}


def duplicate_trip(trip_id, user_id, session_id=None):
    try:
        with _connect() as conn:
            row = conn.execute("SELECT data_json, session_id, title FROM trips "
                               "WHERE trip_id = ? AND user_id = ?", (trip_id, user_id)).fetchone()
            if not row:
                return {"error": "Trip not found"}
            target_session = session_id or row["session_id"]
            owner = conn.execute("SELECT user_id FROM sessions WHERE session_id = ?",
                                 (target_session,)).fetchone()
            if not owner or owner["user_id"] != user_id:
                return {"error": "Session not owned by user"}
            data = json.loads(row["data_json"])
            data.pop("trip_id", None)
            data.pop("version", None)
            return save_new_trip(target_session, data, title=row["title"] + " copy")
    except Exception as exc:
        return {"error": str(exc)}


def trip_versions(trip_id, session_id=None):
    try:
        with _connect() as conn:
            rows = conn.execute(
                "SELECT version, change_summary, created_at FROM trip_versions WHERE trip_id = ? ORDER BY version ASC",
                (trip_id,),
            ).fetchall()
            return [{"version": r["version"], "summary": r["change_summary"], "created_at": r["created_at"]} for r in rows]
    except Exception:
        return []

