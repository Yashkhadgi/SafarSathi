"""Smoke test for P1 Batch B10: Train/Bus info and Stay Area Recommendations."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.transport_ext_tool import get_train_bus_info, get_stay_areas
from tools.registry import execute_tool


def main():
    checks = []

    # 1. Train/bus info
    tb = get_train_bus_info("Delhi", "Jaipur")
    checks.append(("train/bus info returns response", "route_info" in tb or "info" in tb))
    checks.append(("train/bus has IRCTC verification note", "IRCTC" in str(tb)))
    checks.append(("train/bus has no booking links", "http://book" not in str(tb) and "booking.com" not in tb.get("route_info", "")))
    checks.append(("train/bus empty params error", "error" in get_train_bus_info("", "Jaipur")))

    # 2. Stay area recommendations
    stay_udaipur = get_stay_areas("Udaipur", "family")
    checks.append(("stay areas Udaipur returned", "stay_areas" in stay_udaipur or "info" in stay_udaipur))
    checks.append(("stay areas has traveler tip for family", "Family tip" in stay_udaipur.get("traveler_tip", "") or "family" in str(stay_udaipur).lower()))
    checks.append(("stay areas empty city error", "error" in get_stay_areas("")))

    stay_solo = get_stay_areas("Goa", "women_solo")
    checks.append(("stay areas women_solo tip present", "Women solo tip" in stay_solo.get("traveler_tip", "") or "solo" in str(stay_solo).lower()))

    # 3. Registry tool execution
    reg_tb = execute_tool("get_train_bus_info", {"origin": "Mumbai", "destination": "Goa"})
    checks.append(("registry executes get_train_bus_info", "route_info" in reg_tb or "info" in reg_tb))

    reg_stay = execute_tool("get_stay_areas", {"city": "Jaipur", "traveler_type": "backpacker"})
    checks.append(("registry executes get_stay_areas", "stay_areas" in reg_stay or "info" in reg_stay))

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")

    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
