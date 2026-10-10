"""Smoke test for P1 Batch B13: Destination Recommender and Best Time to Visit."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.recommender_tool import recommend_destinations, best_time_to_visit
from tools.registry import execute_tool


def main():
    checks = []

    # 1. Recommend destinations (Python math scoring)
    rec_oct = recommend_destinations(budget_inr=15000, days=4, month=10, mood="peace, spiritual", origin_city="Nagpur", top_n=3)
    checks.append(("recommender returns recommendations", len(rec_oct.get("recommendations", [])) == 3))
    checks.append(("recommender has scores", all("score" in r for r in rec_oct.get("recommendations", []))))
    checks.append(("recommender scores are in descending order",
                   rec_oct["recommendations"][0]["score"] >= rec_oct["recommendations"][1]["score"]))
    checks.append(("recommender has estimated costs", all("estimated_cost_inr" in r for r in rec_oct["recommendations"])))

    # Different inputs produce different outputs
    rec_beach = recommend_destinations(budget_inr=30000, days=5, month=12, mood="beach, party", origin_city="Delhi", top_n=3)
    top_dest = rec_beach["recommendations"][0]["destination"]
    checks.append(("beach query prefers Goa", top_dest == "Goa"))

    # Invalid inputs handled cleanly
    checks.append(("invalid budget error", "error" in recommend_destinations(budget_inr=-100, days=3, month=5, mood="", origin_city="Delhi")))
    checks.append(("invalid month error", "error" in recommend_destinations(budget_inr=10000, days=3, month=15, mood="", origin_city="Delhi")))

    # 2. Best time to visit
    best_taj = best_time_to_visit("Agra")
    checks.append(("best time Agra returns data", "best_months" in best_taj or "best_time_info" in best_taj))

    best_goa = best_time_to_visit("Goa")
    checks.append(("best time Goa returns data", "best_months" in best_goa or "best_time_info" in best_goa))

    # Empty place error
    checks.append(("best time empty place error", "error" in best_time_to_visit("")))

    # 3. Registry tool execution
    reg_rec = execute_tool("recommend_destinations", {
        "budget_inr": 20000, "days": 3, "month": 11, "origin_city": "Mumbai", "mood": "heritage",
    })
    checks.append(("registry executes recommend_destinations", "recommendations" in reg_rec))

    reg_bt = execute_tool("best_time_to_visit", {"place": "Jaipur"})
    checks.append(("registry executes best_time_to_visit", "best_months" in reg_bt or "best_time_info" in reg_bt))

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")

    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
