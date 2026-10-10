"""Session-scoped language override and detected-language persistence."""

from datetime import datetime, timezone

from memory import session_memory

VALID_LANGUAGES = {"auto", "en-IN", "hi-IN", "bn-IN", "ta-IN", "te-IN", "mr-IN", "gu-IN", "kn-IN", "hinglish"}


def _ensure_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_language_preferences (
            session_id TEXT PRIMARY KEY,
            language_code TEXT NOT NULL DEFAULT 'auto',
            detected_language TEXT NOT NULL DEFAULT 'en-IN',
            show_english INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        )
    """)


def get_session_preferences(session_id):
    defaults = {"language_code": "auto", "detected_language": "en-IN", "show_english": False}
    try:
        if not session_id:
            return defaults
        conn = session_memory._get_conn()
        try:
            _ensure_table(conn)
            row = conn.execute(
                "SELECT language_code, detected_language, show_english FROM session_language_preferences WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            conn.commit()
            if not row:
                return defaults
            return {
                "language_code": row["language_code"],
                "detected_language": row["detected_language"],
                "show_english": bool(row["show_english"]),
            }
        finally:
            conn.close()
    except Exception:
        return defaults


def save_session_preferences(session_id, language_code=None, detected_language=None, show_english=None):
    try:
        if not session_id:
            return False
        current = get_session_preferences(session_id)
        language_code = language_code if language_code in VALID_LANGUAGES else current["language_code"]
        detected_language = detected_language or current["detected_language"]
        show_english = current["show_english"] if show_english is None else bool(show_english)
        conn = session_memory._get_conn()
        try:
            _ensure_table(conn)
            conn.execute(
                """INSERT INTO session_language_preferences
                   (session_id, language_code, detected_language, show_english, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(session_id) DO UPDATE SET
                     language_code=excluded.language_code,
                     detected_language=excluded.detected_language,
                     show_english=excluded.show_english,
                     updated_at=excluded.updated_at""",
                (
                    session_id,
                    language_code,
                    detected_language,
                    int(show_english),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception:
        return False
