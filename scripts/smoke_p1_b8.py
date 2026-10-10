"""Smoke test for P1 Batch B8: Area Safety, Medical Help, and Lost Documents."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.safety_tool import get_area_safety, get_medical_help, get_lost_docs_help
from tools.registry import execute_tool


def main():
    checks = []

    # 1. Area safety for known city
    res = get_area_safety("Varanasi", "night")
    checks.append(("area safety Varanasi returned", "safety_tips" in res and "112" in str(res)))
    checks.append(("area safety has emergency numbers", "112" in res.get("emergency_numbers", {}).values()))
    checks.append(("area safety empty city error", "error" in get_area_safety("")))

    # 2. Medical help (disclaimer + emergency numbers, NO dosage)
    med = get_medical_help("altitude sickness", "Leh")
    checks.append(("medical Leh has guidance", "guidance" in med and "108" in str(med)))
    checks.append(("medical has disclaimer", "DISCLAIMER" in med.get("guidance", "")))
    checks.append(("medical has emergency numbers", "108" in med.get("emergency_numbers", {}).values()))
    # Ensure no dosage numbers like mg/ml/dose
    checks.append(("medical has no dosage recommendations", "mg" not in med.get("guidance", "").lower()))
    checks.append(("medical empty city error", "error" in get_medical_help("fever", "")))

    # 3. Lost documents help
    lost_pass = get_lost_docs_help("passport", "Indian")
    checks.append(("lost passport Indian has steps", len(lost_pass.get("steps", [])) >= 2))
    checks.append(("lost passport mentions FIR", any("FIR" in s for s in lost_pass.get("steps", []))))
    checks.append(("lost passport mentions Passport Seva", any("passport" in str(c).lower() for c in lost_pass.get("contacts", []))))

    lost_foreign = get_lost_docs_help("passport", "Foreigner")
    checks.append(("lost passport Foreigner mentions embassy", any("embassy" in s.lower() for s in lost_foreign.get("steps", []))))

    lost_aadhaar = get_lost_docs_help("aadhaar")
    checks.append(("lost aadhaar mentions UIDAI", any("uidai" in str(c).lower() for c in lost_aadhaar.get("contacts", []))))

    lost_card = get_lost_docs_help("credit card")
    checks.append(("lost card mentions block", any("block" in s.lower() for s in lost_card.get("steps", []))))

    # 4. Registry execution
    reg_safety = execute_tool("get_area_safety", {"city": "Delhi"})
    checks.append(("registry executes get_area_safety", "safety_tips" in reg_safety or "error" not in reg_safety))

    reg_med = execute_tool("get_medical_help", {"symptom": "fever", "city": "Jaipur"})
    checks.append(("registry executes get_medical_help", "guidance" in reg_med))

    reg_lost = execute_tool("get_lost_docs_help", {"what_lost": "passport"})
    checks.append(("registry executes get_lost_docs_help", "steps" in reg_lost))

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")

    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
