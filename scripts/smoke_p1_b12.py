"""Smoke test for P1 Batch B12: Theme Trips, Traveler-Type Plans, and Plan B."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.planning_tool import theme_trip_weights, traveler_type_notes, plan_b_alternatives
from tools.registry import execute_tool


def main():
    checks = []

    # 1. Theme trip weights
    spiritual = theme_trip_weights("spiritual")
    checks.append(("spiritual theme returns tags", "priority_tags" in spiritual and "temple" in spiritual["priority_tags"]))

    adventure = theme_trip_weights("adventure")
    checks.append(("adventure theme returns tags", "priority_tags" in adventure and "trek" in adventure["priority_tags"]))

    heritage = theme_trip_weights("heritage")
    checks.append(("heritage theme returns tags", "priority_tags" in heritage and "fort" in heritage["priority_tags"]))

    invalid_theme = theme_trip_weights("invalid_theme_xyz")
    checks.append(("invalid theme returns error and list", "error" in invalid_theme and "valid_themes" in invalid_theme))

    # 2. Traveler-type notes
    senior = traveler_type_notes("senior")
    checks.append(("senior traveler pace is relaxed", senior.get("recommended_pace") == "relaxed"))
    checks.append(("senior traveler has max stops", senior.get("max_stops_per_day") == 2))
    checks.append(("senior traveler has accessibility notes", "accessibility_note" in senior))

    kids = traveler_type_notes("kids")
    checks.append(("kids traveler pace is relaxed", kids.get("recommended_pace") == "relaxed"))

    women = traveler_type_notes("women_solo")
    checks.append(("women_solo traveler has safety tips", "112" in str(women) or "1363" in str(women)))

    # 3. Plan B alternatives
    mock_itinerary = {
        "destination": "Goa",
        "days": [
            {"day": 1, "slots": [{"place": "Baga Beach"}, {"place": "Calangute Beach"}]},
            {"day": 2, "slots": [{"place": "Fort Aguada"}, {"place": "Anjuna Flea Market"}]},
        ],
    }

    # Without rain alert
    plan_b_normal = plan_b_alternatives(mock_itinerary, {})
    checks.append(("plan b normal returns days", len(plan_b_normal.get("days", [])) == 2))
    checks.append(("plan b detects beach activity", plan_b_normal["days"][0].get("activity_type_detected") == "beach"))

    # With rain alert
    plan_b_rain = plan_b_alternatives(mock_itinerary, {"rain_probability": 85, "condition": "heavy rain"})
    checks.append(("plan b rain triggers alert", plan_b_rain.get("rain_triggered") is True))

    # Invalid itinerary
    checks.append(("plan b invalid itinerary error", "error" in plan_b_alternatives({}, {})))

    # 4. Registry tool execution
    reg_theme = execute_tool("theme_trip_weights", {"theme": "wildlife"})
    checks.append(("registry executes theme_trip_weights", "priority_tags" in reg_theme))

    reg_tt = execute_tool("traveler_type_notes", {"traveler_type": "group"})
    checks.append(("registry executes traveler_type_notes", "recommended_pace" in reg_tt))

    reg_planb = execute_tool("plan_b_alternatives", {"itinerary": mock_itinerary, "weather_data": {}})
    checks.append(("registry executes plan_b_alternatives", "days" in reg_planb))

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")

    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
