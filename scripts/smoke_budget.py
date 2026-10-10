"""Offline smoke checks for budget arithmetic and tier comparison."""

from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.budget_tool import compare_budget_tiers, estimate_budget
from tools.registry import TOOL_FUNCTIONS, TOOL_SCHEMAS


def main():
    trip = {"destination": "Udaipur", "days": 3}
    result = estimate_budget(trip, travelers=2, tier="mid")
    checks = []
    checks.append(("estimate succeeds", "error" not in result))
    checks.append(("category sum equals total", sum(result.get("categories", {}).values()) == result.get("total_inr")))
    checks.append(("approx and verification metadata", result.get("approx") is True and result.get("last_verified") == "2026-10-10"))
    checks.append(("per-person and daily values", result.get("per_person_inr", 0) > 0 and result.get("per_person_per_day_inr", 0) > 0))

    group = estimate_budget(trip, travelers=4, tier="mid")
    checks.append(("four travelers increase total", group.get("total_inr", 0) > result.get("total_inr", 0)))
    checks.append(("city stays constrained to KB", "error" in estimate_budget({"destination": "Atlantis", "days": 3}, 2, "mid")))

    comparison = compare_budget_tiers(trip, travelers=2)
    totals = [item["total_inr"] for item in comparison.get("estimates", [])]
    checks.append(("tier comparison ordered", len(totals) == 3 and totals[0] < totals[1] < totals[2]))
    checks.append(("comparison table and recommendation", "| Tier |" in comparison.get("markdown", "") and bool(comparison.get("recommendation"))))
    checks.append(("budget tools registered", {"estimate_budget", "compare_budget_tiers"} <= set(TOOL_FUNCTIONS) & {schema["name"] for schema in TOOL_SCHEMAS}))

    with patch("tools.currency_tool.convert_currency", return_value={"converted_amount": 123.45, "rate": 0.01}):
        converted = estimate_budget(trip, travelers=2, tier="mid", currency="USD")
    checks.append(("optional currency conversion", converted.get("converted_total", {}).get("currency") == "USD"))

    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
