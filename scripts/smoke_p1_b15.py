"""Smoke test for P1 Batch B15: Smart Packing List and Pre-Trip Checklist."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.checklist_tool import smart_packing_list, pre_trip_checklist
from tools.registry import execute_tool


def main():
    checks = []

    # 1. Smart packing list (Goa beach vs Ladakh cold/altitude)
    goa_pack = smart_packing_list("Goa", days=4, activities=["beach"], season="summer")
    checks.append(("Goa packing list generated", "categories" in goa_pack))
    checks.append(("Goa packing list has beach gear", any("swimwear" in str(i).lower() or "sunscreen" in str(i).lower() for cat in goa_pack["categories"].values() for i in cat)))

    ladakh_pack = smart_packing_list("Ladakh", days=7, activities=["trek"], season="winter")
    checks.append(("Ladakh packing list has thermal/winter gear", any("thermal" in str(i).lower() or "fleece" in str(i).lower() for cat in ladakh_pack["categories"].values() for i in cat)))
    checks.append(("Goa and Ladakh lists are differentiated", goa_pack["categories"] != ladakh_pack["categories"]))

    # Monsoon gear
    monsoon_pack = smart_packing_list("Kerala", days=5, season="monsoon")
    checks.append(("Monsoon list has umbrella/raincoat", any("umbrella" in str(i).lower() or "raincoat" in str(i).lower() for cat in monsoon_pack["categories"].values() for i in cat)))

    # Kids / Senior traveler customization
    kids_pack = smart_packing_list("Jaipur", days=3, traveler_type="kids")
    checks.append(("Kids packing list includes child items", any("child" in str(i).lower() or "toy" in str(i).lower() or "snack" in str(i).lower() for cat in kids_pack["categories"].values() for i in cat)))

    # 2. Pre-trip timeline checklist
    chk = pre_trip_checklist(trip_start_date="2026-11-15", destination="Udaipur", is_international=False)
    checks.append(("pre-trip checklist returns stages", len(chk.get("stages", [])) == 4))
    checks.append(("pre-trip checklist has dated labels", any("Nov 2026" in s["timeline_label"] for s in chk.get("stages", []))))
    checks.append(("pre-trip checklist has safety note", "safety_note" in chk))

    intl_chk = pre_trip_checklist(trip_start_date="2026-12-01", destination="Dubai", is_international=True)
    checks.append(("international checklist has passport item", any("passport" in str(t).lower() for s in intl_chk.get("stages", []) for t in s["tasks"])))

    # 3. Registry tool execution
    reg_pack = execute_tool("smart_packing_list", {"destination": "Manali", "days": 5, "season": "winter"})
    checks.append(("registry executes smart_packing_list", "categories" in reg_pack))

    reg_chk = execute_tool("pre_trip_checklist", {"destination": "Varanasi"})
    checks.append(("registry executes pre_trip_checklist", "stages" in reg_chk))

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")

    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
