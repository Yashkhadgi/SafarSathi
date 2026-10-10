"""Show recent disliked answers and common feedback reasons."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory.feedback import feedback_report


def main():
    report = feedback_report()
    if "error" in report:
        print(f"ERROR: {report['error']}")
        return 1
    print("Common dislike reasons:")
    for item in report["reasons"]:
        print(f"- {item['reason'] or 'unspecified'}: {item['count']}")
    print("\nRecent disliked answers:")
    for item in report["worst_answers"]:
        print(f"- [{item['reason'] or 'unspecified'}] {item['content'][:240]}")
        if item["comment"]:
            print(f"  Comment: {item['comment'][:240]}")
        if item["tools_used"]:
            print(f"  Tools: {item['tools_used']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
