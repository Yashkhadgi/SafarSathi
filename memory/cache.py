"""Small per-user SQLite TTL cache for provider responses."""

import hashlib
import json
import logging
import sqlite3
import time
from contextvars import ContextVar
from pathlib import Path


CACHE_PATH = Path(__file__).resolve().parent / "api_cache.db"
_scope = ContextVar("safarsathi_cache_scope", default="global")
_log = logging.getLogger("safarsathi.cache")


def set_scope(user_id):
    return _scope.set(user_id or "global")


def reset_scope(token):
    _scope.reset(token)


def _connect():
    conn = sqlite3.connect(CACHE_PATH, timeout=5)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_cache (
            cache_key TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            value_json TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    return conn


def cached_call(provider, arguments, ttl_seconds, loader):
    """Cache a successful JSON-compatible result; return provider errors unchanged."""
    owner_id = _scope.get()
    cache_key = hashlib.sha256(json.dumps(
        [owner_id, provider, arguments], sort_keys=True, ensure_ascii=False,
        default=str,
    ).encode("utf-8")).hexdigest()
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT value_json FROM api_cache WHERE cache_key = ? AND expires_at > ?",
                (cache_key, time.time()),
            ).fetchone()
            if row:
                _log.info("cache hit provider=%s", provider)
                return json.loads(row[0])
    except sqlite3.Error:
        pass
    result = loader()
    if not result or (isinstance(result, dict) and "error" in result):
        return result
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO api_cache VALUES (?, ?, ?, ?, ?)",
                (cache_key, owner_id, provider,
                 json.dumps(result, ensure_ascii=False, default=str), time.time() + ttl_seconds),
            )
        _log.info("cache miss provider=%s", provider)
    except (sqlite3.Error, TypeError):
        pass
    return result


def delete_user_cache(user_id):
    try:
        with _connect() as conn:
            conn.execute("DELETE FROM api_cache WHERE owner_id = ?", (user_id,))
        return {"deleted": True}
    except sqlite3.Error as exc:
        return {"error": str(exc)}


def cache_stats(user_id):
    try:
        with _connect() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM api_cache WHERE owner_id = ? AND expires_at > ?",
                (user_id, time.time()),
            ).fetchone()[0]
        return {"active_entries": count}
    except sqlite3.Error:
        return {"active_entries": 0}
