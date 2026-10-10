"""Offline account, deletion, cache and rate limit regression checks."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory import cache, session_memory
from memory.auth import browser_user, login_account, logout_account, register_account
from memory.privacy import delete_all_user_data, get_consents, set_consents
from memory.trips import save_new_trip
from memory.usage import check_and_record_message, usage_today


def main():
    original_db, original_cache = session_memory.DB_PATH, cache.CACHE_PATH
    with tempfile.TemporaryDirectory() as directory:
        session_memory.DB_PATH = str(Path(directory) / "sessions.db")
        cache.CACHE_PATH = Path(directory) / "cache.db"
        try:
            account = register_account("one@example.test", "long-password-one", "browser-one")
            user_id = account.get("user_id")
            checks = [("register", bool(user_id))]
            checks.append(("wrong password rejected", "error" in login_account("one@example.test", "wrong", "other-browser")))
            checks.append(("another browser isolated", not browser_user("other-browser")))
            logout_account("browser-one")
            checks.append(("logout removes binding", not browser_user("browser-one")))
            login = login_account("one@example.test", "long-password-one", "browser-one")
            checks.append(("login restores account", login.get("user_id") == user_id))
            chat = session_memory.create_session(user_id)
            session_memory.save_turn(chat, "user", "My private chat")
            trip = save_new_trip(chat, {"destination": "Udaipur", "days": []})
            checks.append(("trip belongs to account", "trip_id" in trip))
            set_consents(user_id, location=True, contacts=False)
            checks.append(("consent persists", get_consents(user_id) == {"location": True, "contacts": False}))
            token = cache.set_scope(user_id)
            calls = []

            def load():
                calls.append(1)
                return {"value": "cached"}

            first = cache.cached_call("weather", ["Udaipur"], 3600, load)
            second = cache.cached_call("weather", ["Udaipur"], 3600, load)
            cache.reset_scope(token)
            checks.append(("cache hit", first == second and len(calls) == 1))
            checks.append(("owner rate check", check_and_record_message(user_id, "hello").get("allowed")))
            checks.append(("usage counter", usage_today(user_id)["calls_today"] == 1))
            for _ in range(29):
                check_and_record_message(user_id, "hello")
            checks.append(("30-message limit", "error" in check_and_record_message(user_id, "one more")))
            checks.append(("other user unaffected", check_and_record_message("other-user", "hello").get("allowed")))
            deleted = delete_all_user_data(user_id)
            with session_memory._get_conn() as conn:
                users_left = conn.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]
                turns_left = conn.execute("SELECT COUNT(*) FROM turns WHERE session_id = ?", (chat,)).fetchone()[0]
                trips_left = conn.execute("SELECT COUNT(*) FROM trips WHERE session_id = ?", (chat,)).fetchone()[0]
            checks.append(("delete removes all rows", deleted.get("deleted") and not (users_left or turns_left or trips_left)))
            checks.append(("delete removes browser binding", not browser_user("browser-one")))
            checks.append(("delete removes cache", cache.cache_stats(user_id)["active_entries"] == 0))
            for label, passed in checks:
                print(f"{'PASS' if passed else 'FAIL'}: {label}")
            return 0 if all(passed for _, passed in checks) else 1
        finally:
            session_memory.DB_PATH, cache.CACHE_PATH = original_db, original_cache


if __name__ == "__main__":
    raise SystemExit(main())
