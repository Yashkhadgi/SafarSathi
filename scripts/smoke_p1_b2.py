"""Offline user profile and saved trip checks."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory import cache, session_memory
from memory.favorites import add_favorite, list_favorites, remove_favorite
from memory.privacy import delete_all_user_data
from memory.profiles import delete_profile, get_profile, save_from_chat, save_profile
from memory.trips import delete_trip, duplicate_trip, list_trips, rename_trip, save_new_trip


def main():
    old_db, old_cache = session_memory.DB_PATH, cache.CACHE_PATH
    with tempfile.TemporaryDirectory() as directory:
        session_memory.DB_PATH = str(Path(directory) / "sessions.db")
        cache.CACHE_PATH = Path(directory) / "cache.db"
        try:
            user = "profile-user"
            other = "other-user"
            chat = session_memory.create_session(user)
            checks = []
            checks.append(("blank profile for new user", not any(get_profile(other).values())))
            saved = save_profile(user, {"diet": "veg", "home_city": "Nagpur"})
            checks.append(("profile saved", saved.get("diet") == "veg"))
            checks.append(("profile isolated", not get_profile(other).get("diet")))
            save_from_chat(user, "Main vegan hoon")
            checks.append(("chat profile update", get_profile(user).get("diet") == "vegan"))
            trip = save_new_trip(chat, {"destination": "Udaipur", "days": []})
            copied = duplicate_trip(trip["trip_id"], user)
            checks.append(("duplicate has new id", copied.get("trip_id") not in (None, trip["trip_id"])))
            renamed = rename_trip(trip["trip_id"], user, "October trip")
            checks.append(("rename retained", renamed.get("renamed") and any(
                row["title"] == "October trip" for row in list_trips(user))))
            checks.append(("other user cannot view", not list_trips(other)))
            checks.append(("other user cannot delete", "error" in delete_trip(trip["trip_id"], other)))
            checks.append(("favorite saved", add_favorite(user, "City Palace").get("saved")))
            checks.append(("favorite isolated", not list_favorites(other)))
            checks.append(("favorite removed", remove_favorite(user, "City Palace").get("deleted")))
            checks.append(("trip deleted", delete_trip(trip["trip_id"], user).get("deleted")))
            checks.append(("profile deleted", delete_profile(user).get("deleted") and not any(get_profile(user).values())))
            save_profile(user, {"diet": "veg"})
            add_favorite(user, "Hawa Mahal")
            deleted = delete_all_user_data(user)
            checks.append(("privacy deletion covers B2", deleted.get("deleted") and
                           not any(get_profile(user).values()) and not list_favorites(user) and not list_trips(user)))
            for label, passed in checks:
                print(f"{'PASS' if passed else 'FAIL'}: {label}")
            return 0 if all(passed for _, passed in checks) else 1
        finally:
            session_memory.DB_PATH, cache.CACHE_PATH = old_db, old_cache


if __name__ == "__main__":
    raise SystemExit(main())
