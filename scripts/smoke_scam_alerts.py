"""Offline checks for sourced scam alerts and automatic answer attachment."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.scam_alerts import auto_attach_scam_alerts
from tools.registry import execute_tool
from tools.scam_tool import known_scam_cities


def main():
    result = execute_tool("get_scam_alerts", {"city": "Agra", "context": "airport transfer"})
    alerts = result.get("alerts", [])
    valid = len(alerts) >= 3 and all(
        alert.get("what_to_do")
        and alert.get("fair_price_hint")
        and alert.get("last_verified") == "2026-10-10"
        and alert.get("sources")
        for alert in alerts
    )
    print("PASS registry returns sourced actions" if valid else f"FAIL registry result: {result}")

    answer = auto_attach_scam_alerts("Take a prepaid taxi from the airport.", "Agra airport taxi to hotel")
    attached = "Sourced scam and tourist-trap alerts for Agra" in answer and "What to do" in answer
    print("PASS relevant alert auto-attaches" if attached else "FAIL relevant alert auto-attach")

    plain = auto_attach_scam_alerts("Agra has several historic sites.", "Tell me about Agra history")
    no_false_positive = plain == "Agra has several historic sites."
    print("PASS unrelated answer stays unchanged" if no_false_positive else "FAIL unrelated answer changed")

    cities_ok = bool(known_scam_cities())
    for city in known_scam_cities():
        city_result = execute_tool("get_scam_alerts", {"city": city, "context": "taxi guide shopping"})
        city_alerts = city_result.get("alerts", [])
        cited_names = {source["source_name"] for alert in city_alerts for source in alert.get("sources", [])}
        cities_ok = cities_ok and len(city_alerts) >= 3 and len(cited_names) >= 2
    print("PASS all KB cities have 3+ alerts and 2+ sources" if cities_ok else "FAIL city alert/source coverage")
    return 0 if valid and attached and no_false_positive and cities_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
