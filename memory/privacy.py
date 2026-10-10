"""Per-user consent and complete local data deletion."""

import sqlite3

from memory import session_memory


def _connect():
    conn = session_memory._get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_consents (
            user_id TEXT PRIMARY KEY,
            location INTEGER NOT NULL DEFAULT 0,
            contacts INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    return conn


def get_consents(user_id):
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT location, contacts FROM user_consents WHERE user_id = ?", (user_id,)
            ).fetchone()
            return {"location": bool(row["location"]), "contacts": bool(row["contacts"])} if row else {
                "location": False, "contacts": False,
            }
    except Exception:
        return {"location": False, "contacts": False}


def set_consents(user_id, location, contacts):
    try:
        with _connect() as conn:
            session_memory.ensure_user(conn, user_id)
            conn.execute(
                "INSERT INTO user_consents VALUES (?, ?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET location=excluded.location, contacts=excluded.contacts",
                (user_id, int(bool(location)), int(bool(contacts))),
            )
        return {"saved": True}
    except Exception as exc:
        return {"error": str(exc)}


def delete_all_user_data(user_id):
    """Delete account, sessions and dependent rows in one transaction."""
    try:
        with _connect() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            sessions = [row[0] for row in conn.execute(
                "SELECT session_id FROM sessions WHERE user_id = ?", (user_id,)
            )]
            tables = {row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )}
            for session_id in sessions:
                if "feedback" in tables:
                    conn.execute("DELETE FROM feedback WHERE session_id = ?", (session_id,))
                if "trip_versions" in tables and "trips" in tables:
                    conn.execute("DELETE FROM trip_versions WHERE trip_id IN "
                                 "(SELECT trip_id FROM trips WHERE session_id = ?)", (session_id,))
                if "trips" in tables:
                    conn.execute("DELETE FROM trips WHERE session_id = ?", (session_id,))
                for table in ("session_language_preferences", "turns"):
                    if table in tables:
                        conn.execute(f"DELETE FROM {table} WHERE session_id = ?", (session_id,))
            for table in ("trusted_contacts", "user_consents", "browser_auth", "accounts",
                          "profiles", "favorites"):
                if table in tables:
                    conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
            if "usage_events" in tables:
                conn.execute("DELETE FROM usage_events WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        from memory.cache import delete_user_cache

        cache_result = delete_user_cache(user_id)
        if "error" in cache_result:
            return cache_result
        from ui.live_translation import delete_user_audio

        audio_result = delete_user_audio(user_id)
        if "error" in audio_result:
            return audio_result
        return {"deleted": True}
    except sqlite3.Error as exc:
        return {"error": str(exc)}
