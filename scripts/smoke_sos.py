"""Offline checks for static SOS content and fail-closed Maps behavior."""

import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.maps_tool import nearest_emergency_services


def main():
    path = Path(__file__).resolve().parents[1] / "data" / "emergency" / "india.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    numbers = {item["number"] for item in data["numbers"]}
    required = {"112", "100", "101", "102 / 108", "1091", "1363", "1098"}
    checks = [
        ("static numbers present", required <= numbers),
        ("last verified date present", bool(data.get("last_verified"))),
        ("static Hindi phrase present", bool(data.get("hindi_emergency_phrase"))),
        ("share-location hook present", data.get("share_location_hook") == "trusted_contacts_share_location"),
    ]
    with patch("tools.maps_tool._client", side_effect=RuntimeError("Maps unavailable")):
        fallback = nearest_emergency_services(city="Jaipur")
    checks.append(("Maps failure returns empty nearby results", fallback == {"hospitals": [], "police": []}))
    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
