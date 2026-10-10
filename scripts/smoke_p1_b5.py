"""Offline map rendering, filtering, and ownership checks."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory import session_memory
from memory.trips import save_new_trip
from tools.map_view import geocode_osm, map_points, render_map_html, trip_map


def check(label, ok):
    print(f"{'PASS' if ok else 'FAIL'} {label}")
    return bool(ok)


def main():
    passed = []
    trip = {"destination": "Test City", "days": [
        {"day": day, "slots": [
            {"place": f"Stop {day}-{stop}", "time": "10:00",
             "map_coordinates": {"lat": 20 + day * .01, "lng": 78 + stop * .01,
                                 "source": "OpenStreetMap"}}
            for stop in range(5)]}
        for day in range(1, 6)]}
    positions = map_points(trip)
    passed.append(check("25 mapped stops", len(positions["points"]) == 25))
    all_map = render_map_html(positions["points"])
    day_map = render_map_html(positions["points"], "2")
    passed.append(check("sandboxed map and OSM attribution", "sandbox=&#x27;allow-scripts&#x27;" not in all_map
                        and "sandbox='allow-scripts'" in all_map and "OpenStreetMap" in all_map))
    passed.append(check("day filter reduces payload", "Stop 2-0" in day_map
                        and "Stop 1-0" not in day_map))
    passed.append(check("trip map returns source", trip_map(trip, "all")["mapped"] == 25))

    response = Mock()
    response.json.return_value = [{"lat": "26.9", "lon": "75.8", "display_name": "Jaipur",
                                   "osm_type": "node", "osm_id": 123}]
    with patch("tools.map_view.cached_call", side_effect=lambda _n, _k, _t, loader: loader()), \
         patch("tools.map_view.requests.get", return_value=response):
        geocoded = geocode_osm("Jaipur, India")
    passed.append(check("OSM geocoder source", geocoded.get("source_url") ==
                        "https://www.openstreetmap.org/node/123"))

    old_db = session_memory.DB_PATH
    with tempfile.TemporaryDirectory() as tmp:
        session_memory.DB_PATH = str(Path(tmp) / "sessions.db")
        try:
            session = session_memory.create_session("map-owner")
            saved = save_new_trip(session, trip)
            from memory.trips import get_trip

            passed.append(check("map trip user isolation", "error" in get_trip(
                saved["trip_id"], user_id="other-user")))
        finally:
            session_memory.DB_PATH = old_db
    return 0 if all(passed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
