"""Smoke test for P1 Batch B14: Multi-City Optimizer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.optimizer_tool import optimize_route
from tools.registry import execute_tool


def main():
    checks = []

    # 1. Multi-city optimization (Nagpur -> Shirdi, Nashik, Aurangabad, 6 days)
    cities = ["Shirdi", "Nashik", "Aurangabad"]
    opt = optimize_route(cities=cities, origin="Nagpur", total_days=6)

    checks.append(("optimizer returns optimized order", "optimized_order" in opt))
    checks.append(("optimizer includes origin as start", opt.get("optimized_order", [])[0] == "Nagpur"))
    checks.append(("optimizer visits all requested cities", len(opt.get("optimized_order", [])) == 4))
    checks.append(("optimizer allocates 6 days total",
                   sum(d["days_allocated"] for d in opt.get("day_allocations", [])) == 6))
    checks.append(("optimizer has inter-city legs with km", len(opt.get("inter_city_legs", [])) == 3))
    checks.append(("optimizer total km is positive", opt.get("total_km_approx", 0) > 0))
    checks.append(("optimizer includes disclaimer", "disclaimer" in opt))

    # 2. Golden Triangle (Delhi -> Agra, Jaipur)
    gt = optimize_route(cities=["Jaipur", "Agra"], origin="Delhi", total_days=5)
    checks.append(("golden triangle returns order", len(gt.get("optimized_order", [])) == 3))
    checks.append(("golden triangle day sum equals 5",
                   sum(d["days_allocated"] for d in gt.get("day_allocations", [])) == 5))

    # 3. Error handling
    checks.append(("empty cities returns error", "error" in optimize_route([], "Delhi", 5)))
    checks.append(("empty origin returns error", "error" in optimize_route(["Agra"], "", 5)))
    checks.append(("invalid days returns error", "error" in optimize_route(["Agra"], "Delhi", -2)))

    # 4. Registry tool execution
    reg_opt = execute_tool("optimize_route", {
        "cities": ["Udaipur", "Jodhpur", "Jaisalmer"],
        "origin": "Jaipur",
        "total_days": 7,
    })
    checks.append(("registry executes optimize_route", "optimized_order" in reg_opt))

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")

    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
