"""Offline trip persistence and patch safety checks."""

import tempfile
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory import session_memory
from tools.itinerary_tool import build_itinerary, edit_itinerary


def main():
    original_db = session_memory.DB_PATH
    places = [
        {"name": f"Place {n}", "source_name": "Test source",
         "source_url": "https://example.org/source", "last_verified": "2026-10-10"}
        for n in range(4)
    ]
    with tempfile.TemporaryDirectory() as directory:
        session_memory.DB_PATH = str(Path(directory) / "sessions.db")
        try:
            session_id = session_memory.create_session("trip-user")
            with patch("tools.itinerary_tool.distance_and_time", return_value={"duration_text": "15 min"}), \
                 patch("tools.itinerary_tool._hours_note", return_value=("verify opening hours and closed days", "")):
                trip = build_itinerary("Test City", 2, travelers=2,
                                       pace="relaxed", session_id=session_id, places=places)
            initial = "error" not in trip and len(trip["days"]) == 2
            print("PASS trip saved" if initial else f"FAIL trip saved: {trip}")
            if not initial:
                return 1
            before = trip["days"][0]["slots"][0]["place"]
            swapped = edit_itinerary(trip["trip_id"], "swap", session_id,
                                     operations=[{"op": "swap_days", "day_a": 1, "day_b": 2}])
            swapped_ok = "error" not in swapped and swapped["version"] == 2 and swapped["days"][0]["slots"][0]["place"] != before
            print("PASS versioned swap" if swapped_ok else f"FAIL versioned swap: {swapped}")
            undone = edit_itinerary(trip["trip_id"], "undo", session_id)
            undo_ok = "error" not in undone and undone["version"] == 3 and undone["days"][0]["slots"][0]["place"] == before
            print("PASS undo" if undo_ok else f"FAIL undo: {undone}")
            other_session = session_memory.create_session("other-user")
            isolated = "error" in edit_itinerary(trip["trip_id"], "undo", other_session)
            print("PASS session isolation" if isolated else "FAIL session isolation")
            return 0 if swapped_ok and undo_ok and isolated else 1
        finally:
            session_memory.DB_PATH = original_db


if __name__ == "__main__":
    raise SystemExit(main())
