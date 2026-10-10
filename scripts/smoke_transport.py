"""Offline smoke checks for the Batch B7 transport tools and registry."""

from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import registry, transport_tools


def main():
    checks = []
    checks.append((
        "tool schemas registered",
        {"how_to_reach", "get_local_transport"}
        <= {schema["name"] for schema in registry.TOOL_SCHEMAS},
    ))

    sample_route = {
        "origin": "Nagpur", "destination": "Shirdi",
        "rows": [{"mode": "Road", "duration": "verify", "distance": "verify", "approx_cost": "verify", "notes": "missing map data", "source": ""}],
        "nearest_airport": "verify", "nearest_railway_station": "verify",
        "recommendation": "Verify route data.",
        "verify_line": "Verify on IRCTC or airline/operator sites; no booking links.",
        "sources": [], "markdown": "verify",
    }
    with patch.object(transport_tools, "_cache_get", return_value=None), \
         patch.object(transport_tools, "_route_response", return_value=sample_route), \
         patch.object(transport_tools, "_cache_set"):
        route = transport_tools.how_to_reach("Nagpur", "Shirdi")
    checks.append(("route missing data marked verify", route["rows"][0]["duration"] == "verify"))
    checks.append(("route has no booking links", "booking links" in route["verify_line"].lower()))

    cache = {}
    route_calls = []

    def cache_get(origin, destination):
        result = cache.get((origin, destination))
        return dict(result) if result is not None else None

    def cache_set(origin, destination, result):
        cache[(origin, destination)] = result

    def route_factory(origin, destination):
        route_calls.append((origin, destination))
        return dict(sample_route, origin=origin, destination=destination, markdown="cached-route")

    with patch.object(transport_tools, "_cache_get", side_effect=cache_get), \
         patch.object(transport_tools, "_cache_set", side_effect=cache_set), \
         patch.object(transport_tools, "_route_response", side_effect=route_factory):
        first = transport_tools.how_to_reach("Cache Test Origin", "Cache Test Destination")
        second = transport_tools.how_to_reach("Cache Test Origin", "Cache Test Destination")
    checks.append(("24-hour cache second call hit", first["cache"] == "miss" and second["cache"] == "hit"))
    checks.append(("route computation reused cached result", len(route_calls) == 1))

    goa_record = {
        "text": "Goa local buses cost approx INR 10 for 2-3 km; verify current fares.",
        "source_name": "Goa Tourism Development Corporation",
        "source_url": "https://goa-tourism.com/media-room/getting-around/",
    }
    with patch.object(transport_tools, "_kb_records", return_value=[goa_record]):
        local = transport_tools.get_local_transport("Goa")
    checks.append(("local transport includes fare guidance", "approx" in local["options"][0]["fare_range"].lower()))
    checks.append(("local transport carries source", local["options"][0]["source_url"].startswith("https://")))

    with patch.object(transport_tools, "_kb_records", return_value=[]), \
         patch.object(transport_tools, "_web_search", return_value=[]):
        fallback = transport_tools.get_local_transport("Unlisted place")
    checks.append(("empty fallback does not fabricate options", fallback["grounded"] is False))

    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
