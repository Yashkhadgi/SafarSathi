"""Optional local accounts bound to a Gradio browser session."""

import hashlib
import hmac
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone

from memory import session_memory


def _now():
    return datetime.now(timezone.utc).isoformat()


def _connect():
    conn = session_memory._get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL,
            salt BLOB NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS browser_auth (
            session_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    return conn


def _digest(password: str, salt: bytes) -> bytes:
    """PBKDF2-HMAC-SHA256; works on both OpenSSL and LibreSSL (macOS)."""
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations=200_000)


def register_account(email, password, session_hash):
    try:
        email = str(email or "").strip().casefold()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            return {"error": "Enter a valid email address"}
        if len(password or "") < 10:
            return {"error": "Use a password of at least 10 characters"}
        if not session_hash:
            return {"error": "Browser session unavailable"}
        user_id = "account-" + uuid.uuid4().hex
        salt = os.urandom(16)
        with _connect() as conn:
            session_memory.ensure_user(conn, user_id)
            conn.execute(
                "INSERT INTO accounts VALUES (?, ?, ?, ?, ?)",
                (user_id, email, _digest(password, salt), salt, _now()),
            )
            conn.execute(
                "INSERT OR REPLACE INTO browser_auth VALUES (?, ?, ?)",
                (session_hash, user_id, _now()),
            )
        return {"user_id": user_id}
    except sqlite3.IntegrityError:
        return {"error": "This email is already registered"}
    except Exception as exc:
        return {"error": str(exc)}


def login_account(email, password, session_hash):
    try:
        if not session_hash:
            return {"error": "Browser session unavailable"}
        with _connect() as conn:
            row = conn.execute(
                "SELECT user_id, password_hash, salt FROM accounts WHERE email = ?",
                (str(email or "").strip().casefold(),),
            ).fetchone()
            if row is None or not hmac.compare_digest(_digest(password or "", row["salt"]), row["password_hash"]):
                return {"error": "Email or password is incorrect"}
            conn.execute(
                "INSERT OR REPLACE INTO browser_auth VALUES (?, ?, ?)",
                (session_hash, row["user_id"], _now()),
            )
            return {"user_id": row["user_id"]}
    except Exception as exc:
        return {"error": str(exc)}


def browser_user(session_hash):
    try:
        if not session_hash:
            return ""
        with _connect() as conn:
            row = conn.execute(
                "SELECT user_id FROM browser_auth WHERE session_hash = ?", (session_hash,)
            ).fetchone()
            return row["user_id"] if row else ""
    except Exception:
        return ""


def logout_account(session_hash):
    try:
        with _connect() as conn:
            conn.execute("DELETE FROM browser_auth WHERE session_hash = ?", (session_hash,))
        return {"logged_out": True}
    except Exception as exc:
        return {"error": str(exc)}
