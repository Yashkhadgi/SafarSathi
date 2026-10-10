"""User-owned saved places."""

from datetime import datetime, timezone

from memory import session_memory


def _connect():
    conn = session_memory._get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            user_id TEXT NOT NULL,
            place TEXT NOT NULL,
            source_url TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (user_id, place),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    return conn


def add_favorite(user_id, place, source_url=""):
    try:
        place = str(place or "").strip()
        if not place or len(place) > 100:
            return {"error": "Enter a place name"}
        if source_url and not str(source_url).startswith("https://"):
            return {"error": "Source URL must use HTTPS"}
        with _connect() as conn:
            session_memory.ensure_user(conn, user_id)
            conn.execute("INSERT OR REPLACE INTO favorites VALUES (?, ?, ?, ?)",
                         (user_id, place, source_url or "", datetime.now(timezone.utc).isoformat()))
        return {"saved": True}
    except Exception as exc:
        return {"error": str(exc)}


def list_favorites(user_id):
    try:
        with _connect() as conn:
            rows = conn.execute("SELECT place, source_url FROM favorites WHERE user_id = ? "
                                "ORDER BY created_at DESC", (user_id,)).fetchall()
            return [{"place": row["place"], "source_url": row["source_url"]} for row in rows]
    except Exception:
        return []


def remove_favorite(user_id, place):
    try:
        with _connect() as conn:
            cursor = conn.execute("DELETE FROM favorites WHERE user_id = ? AND place = ?",
                                  (user_id, place))
        return {"deleted": cursor.rowcount > 0}
    except Exception as exc:
        return {"error": str(exc)}
