"""Optional traveler preferences, stored per user."""

import json
import re
from datetime import datetime, timezone

from memory import session_memory


FIELDS = ("interests", "diet", "allergies", "budget_range", "mobility",
          "languages", "home_city", "travel_style")
DIETS = {"", "veg", "vegan", "jain", "halal", "no_restriction"}


def _connect():
    conn = session_memory._get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id TEXT PRIMARY KEY,
            profile_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    return conn


def get_profile(user_id):
    try:
        with _connect() as conn:
            row = conn.execute("SELECT profile_json FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
            return json.loads(row["profile_json"]) if row else {field: "" for field in FIELDS}
    except Exception:
        return {field: "" for field in FIELDS}


def save_profile(user_id, updates):
    try:
        if not isinstance(updates, dict):
            return {"error": "Profile fields must be an object"}
        profile = get_profile(user_id)
        for field, value in updates.items():
            if field not in FIELDS:
                return {"error": f"Unknown profile field: {field}"}
            if not isinstance(value, str) or len(value) > 500:
                return {"error": f"Invalid {field}"}
            if field == "diet" and value not in DIETS:
                return {"error": "Invalid diet choice"}
            profile[field] = value.strip()
        with _connect() as conn:
            session_memory.ensure_user(conn, user_id)
            conn.execute(
                "INSERT INTO profiles VALUES (?, ?, ?) ON CONFLICT(user_id) "
                "DO UPDATE SET profile_json=excluded.profile_json, updated_at=excluded.updated_at",
                (user_id, json.dumps(profile, ensure_ascii=False), datetime.now(timezone.utc).isoformat()),
            )
        return profile
    except Exception as exc:
        return {"error": str(exc)}


def delete_profile(user_id):
    try:
        with _connect() as conn:
            conn.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
        return {"deleted": True}
    except Exception as exc:
        return {"error": str(exc)}


def profile_summary(user_id):
    profile = get_profile(user_id)
    parts = [f"{field}: {value}" for field, value in profile.items() if value]
    return "; ".join(parts)[:800]


def save_from_chat(user_id, message):
    """Handle only explicit diet self-statements; do not infer from a food query."""
    lower = str(message or "").casefold()
    patterns = (
        (r"\b(?:main|mai|i am|i'm)\s+(?:a\s+)?vegan\b", "vegan"),
        (r"\b(?:(?:main|mai|i am|i'm)\s+(?:a\s+)?)?(?:veg|vegetarian)\s+hoon\b|"
         r"\b(?:i am|i'm)\s+(?:a\s+)?(?:veg|vegetarian)\b", "veg"),
        (r"\b(?:main|mai|i am|i'm)\s+(?:a\s+)?jain\b", "jain"),
        (r"\b(?:main|mai|i am|i'm)\s+(?:a\s+)?halal\b", "halal"),
    )
    for pattern, diet in patterns:
        if re.search(pattern, lower):
            return save_profile(user_id, {"diet": diet})
    return None
