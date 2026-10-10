"""Smoke test for P1 Batch B9: Entry Fees, Fair-Price Guide, and Currency/ATM Tools."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.entry_fees_tool import get_entry_fees
from tools.budget_ext_tool import check_fair_price, atm_info
from tools.registry import execute_tool


def main():
    checks = []

    # 1. Entry fees for known monument
    taj = get_entry_fees("Taj Mahal")
    checks.append(("entry fees Taj Mahal found", len(taj.get("results", [])) > 0))
    if taj.get("results"):
        first = taj["results"][0]
        checks.append(("entry fee has approx flag", first.get("approx") is True))
        checks.append(("entry fee has last_verified", bool(first.get("last_verified"))))
        checks.append(("entry fee has indian and foreigner rates", "entry_fee_indian_inr" in first and "entry_fee_foreign_inr_approx" in first))

    # Multiple monuments match city
    delhi = get_entry_fees("Delhi")
    checks.append(("entry fees Delhi returns monuments", len(delhi.get("results", [])) >= 2))

    # Empty place error
    checks.append(("entry fees empty place error", "error" in get_entry_fees("")))

    # 2. Fair-price guide
    jaipur_price = check_fair_price("Jaipur", "auto")
    checks.append(("fair price Jaipur returns prices", "prices" in jaipur_price and jaipur_price.get("approx") is True))
    checks.append(("fair price has last_verified", bool(jaipur_price.get("last_verified"))))
    checks.append(("fair price empty city error", "error" in check_fair_price("")))

    # 3. ATM information
    leh_atm = atm_info("Leh")
    checks.append(("ATM info Leh has specific advice", "Leh" in leh_atm.get("city_specific", "") or "general" in leh_atm.get("general_atm_info", "").lower()))
    checks.append(("ATM info general advice present", bool(leh_atm.get("general_atm_info"))))

    # 4. Registry tool execution
    reg_fees = execute_tool("get_entry_fees", {"place": "Amber Fort"})
    checks.append(("registry executes get_entry_fees", "results" in reg_fees or "message" in reg_fees))

    reg_price = execute_tool("check_fair_price", {"city": "Delhi", "transport_type": "auto"})
    checks.append(("registry executes check_fair_price", "prices" in reg_price or "message" in reg_price))

    reg_atm = execute_tool("atm_info", {"city": "Goa"})
    checks.append(("registry executes atm_info", "general_atm_info" in reg_atm))

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")

    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
