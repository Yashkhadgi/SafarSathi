"""Dependency-light smoke checks for B5 answer post-processing."""

from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.guardrails import post_process_answer


def main():
    checks = []
    volatile = post_process_answer(
        "Amber Fort ticket price is listed here. Sources: [1] Official (https://example.org)\nLast verified: 2025-01-01",
        user_message="What is the ticket price?",
        today=date(2026, 10, 10),
    )
    checks.append(("volatile approximation", "approx" in volatile.lower()))
    checks.append(("stale-source warning", "six months old" in volatile.lower()))
    checks.append(("footer confidence", "Confidence:" in volatile and "Last verified:" in volatile))
    failed_live = post_process_answer("Could not fetch current forecast.", tool_results=[{"error": "missing key"}])
    checks.append(("tool failure disclosure", "live data was unavailable" in failed_live.lower()))
    safe = post_process_answer("Please move to a safe public place.", user_message="I was robbed, help")
    checks.append(("safety disclaimer", "immediate danger" in safe.lower()))
    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
