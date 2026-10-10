"""Offline checks for P1 B4 provider handling and itinerary conflicts."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory import session_memory
from tools import realtime_tool
from tools.itinerary_tool import build_itinerary
from tools.registry import TOOL_FUNCTIONS


def check(label, condition):
    print(f"{'PASS' if condition else 'FAIL'} {label}")
    return bool(condition)


def main():
    passed = []
    passed.append(check("B4 tools registered", all(
        name in TOOL_FUNCTIONS for name in ("get_live_weather", "get_opening_hours", "near_me"))))
    with patch.object(realtime_tool, "OPENWEATHER_API_KEY", ""):
        passed.append(check("weather missing key", "error" in realtime_tool.get_live_weather("Jaipur")))
    with patch.object(realtime_tool, "GOOGLE_MAPS_API_KEY", ""):
        passed.append(check("hours missing key", "error" in realtime_tool.get_opening_hours(
            "Taj Mahal", "Agra", "2026-10-12")))
    passed.append(check("nearby requires consent", "error" in realtime_tool.near_me(
        26.9, 75.8, consent=False)))
    passed.append(check("AQI provider scales stay separate",
                        realtime_tool.air_quality_advice(4) and
                        realtime_tool.air_quality_advice(300, "us") and
                        not realtime_tool.air_quality_advice(3)))

    forecast = {"list": [{"dt_txt": "2026-10-12 12:00:00", "main": {"temp": 41},
                          "weather": [{"description": "rain"}]}]}
    current = {"main": {"temp": 41}, "weather": [{"description": "rain"}],
               "coord": {"lat": 26.9, "lon": 75.8}}
    air = {"list": [{"main": {"aqi": 4}, "components": {"pm2_5": 34}}]}
    responses = [Mock(json=Mock(return_value=item)) for item in (forecast, current, air)]
    with patch.object(realtime_tool, "OPENWEATHER_API_KEY", "test"), \
         patch.object(realtime_tool, "cached_call", side_effect=lambda _n, _k, _t, loader: loader()), \
         patch.object(realtime_tool.requests, "get", side_effect=responses):
        weather = realtime_tool.get_live_weather("Jaipur")
    passed.append(check("weather/AQI warnings", weather.get("air_quality", {}).get("scale") ==
                        "OpenWeather 1-5" and len(weather.get("warnings", [])) >= 3))

    maps = Mock()
    maps.places.return_value = {"results": [{"place_id": "place-1"}]}
    maps.place.return_value = {"result": {"name": "Example Museum",
                                          "opening_hours": {"weekday_text": [
                                              "Monday: Closed", "Tuesday: 10:00 AM - 5:00 PM"]}}}
    with patch.object(realtime_tool, "GOOGLE_MAPS_API_KEY", "test"), \
         patch.object(realtime_tool, "cached_call", side_effect=lambda _n, _k, _t, loader: loader()), \
         patch("tools.maps_tool._client", return_value=maps):
        hours = realtime_tool.get_opening_hours("Example Museum", "City", "2026-10-12")
    passed.append(check("closed Monday detected", hours.get("closed") is True))

    maps.places_nearby.return_value = {"results": [
        {"name": "Far", "rating": 4.2, "geometry": {"location": {"lat": 26.95, "lng": 75.8}}},
        {"name": "Near", "rating": 4.5, "geometry": {"location": {"lat": 26.91, "lng": 75.8}}},
    ]}
    with patch.object(realtime_tool, "GOOGLE_MAPS_API_KEY", "test"), \
         patch.object(realtime_tool, "cached_call", side_effect=lambda _n, _k, _t, loader: loader()), \
         patch("tools.maps_tool._client", return_value=maps):
        nearby = realtime_tool.near_me(26.9, 75.8, kind="attractions", min_rating=4,
                                       consent=True)
    passed.append(check("nearby distance order", [row["name"] for row in nearby.get("results", [])]
                        == ["Near", "Far"]))

    old_db = session_memory.DB_PATH
    places = [{"name": "Example Museum", "source_name": "Official", "source_url":
               "https://example.org", "last_verified": "2026-10-10"}]
    with tempfile.TemporaryDirectory() as tmp:
        session_memory.DB_PATH = str(Path(tmp) / "sessions.db")
        try:
            session = session_memory.create_session("b4-user")
            with patch("tools.itinerary_tool.distance_and_time", return_value={}), \
                 patch("tools.itinerary_tool._hours_note", return_value=("verify opening hours and closed days", "")), \
                 patch("tools.realtime_tool.get_opening_hours", return_value=hours):
                trip = build_itinerary("City", 1, session_id=session, places=places,
                                       start_date="2026-10-12")
            passed.append(check("dated trip flags closure", any(
                "listed closed" in warning for warning in trip.get("warnings", []))))
        finally:
            session_memory.DB_PATH = old_db
    return 0 if all(passed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
