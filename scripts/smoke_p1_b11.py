"""Smoke test for P1 Batch B11: Food Guide, Temple Guide, and Etiquette."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.knowledge_tool import get_food_guide, get_temple_guide, get_etiquette
from tools.registry import execute_tool


def main():
    checks = []

    # 1. Food guide
    food_lucknow = get_food_guide("Lucknow", "veg")
    checks.append(("food guide Lucknow returned", "food_guide" in food_lucknow or "info" in food_lucknow))
    checks.append(("food guide has allergy disclaimer", "ALLERGY" in food_lucknow.get("food_guide", "") or "disclaimer" in food_lucknow))
    checks.append(("food guide empty city error", "error" in get_food_guide("")))

    food_vegan = get_food_guide("Goa", "vegan")
    checks.append(("food guide vegan has note", bool(food_vegan.get("diet_note")) or "vegan" in str(food_vegan).lower()))

    # 2. Temple guide
    temple = get_temple_guide("Kashi Vishwanath")
    checks.append(("temple guide returns information", "guide" in temple or "info" in temple))
    checks.append(("temple guide empty query error", "error" in get_temple_guide("")))

    # 3. Etiquette guide
    etiquette_punjab = get_etiquette("Punjab")
    checks.append(("etiquette Punjab returned", "guidelines" in etiquette_punjab))

    etiquette_general = get_etiquette("")
    checks.append(("etiquette general India fallback works", "guidelines" in etiquette_general))

    # 4. Registry tool execution
    reg_food = execute_tool("get_food_guide", {"city": "Amritsar", "diet_filter": "veg"})
    checks.append(("registry executes get_food_guide", "food_guide" in reg_food or "info" in reg_food))

    reg_temple = execute_tool("get_temple_guide", {"site_or_city": "Golden Temple"})
    checks.append(("registry executes get_temple_guide", "guide" in reg_temple or "info" in reg_temple))

    reg_etiq = execute_tool("get_etiquette", {"state_or_religion": "Rajasthan"})
    checks.append(("registry executes get_etiquette", "guidelines" in reg_etiq))

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")

    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
