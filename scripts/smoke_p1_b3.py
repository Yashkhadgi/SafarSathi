"""Offline streaming and feedback checks."""

import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.core_agent import stream_core_agent
from memory import cache, session_memory
from memory.feedback import feedback_report, save_feedback
from memory.privacy import delete_all_user_data


def main():
    old_db, old_cache = session_memory.DB_PATH, cache.CACHE_PATH
    with tempfile.TemporaryDirectory() as directory:
        session_memory.DB_PATH = str(Path(directory) / "sessions.db")
        cache.CACHE_PATH = Path(directory) / "cache.db"
        try:
            user, other = "feedback-user", "other-user"
            session = session_memory.create_session(user)
            session_memory.save_turn(session, "user", "Tell me about Jaipur")
            session_memory.save_turn(session, "assistant", "A sourced reply\nUsed: search_knowledge_base")
            saved = save_feedback(user, session, 0, -1, "wrong_info", "Wrong place")
            checks = [("dislike stored", saved.get("saved")),
                      ("cross-user feedback refused", "error" in save_feedback(other, session, 0, -1)),
                      ("report includes reason", feedback_report()["reasons"][0]["reason"] == "wrong_info")]

            answer = SimpleNamespace(content=[SimpleNamespace(type="text", text="Hello traveler")])

            def mock_stream(*args, **kwargs):
                yield {"text": "Hello"}
                yield {"text": " traveler"}
                yield {"response": answer}

            with patch("agents.core_agent.stream_llm_with_tools", side_effect=mock_stream):
                events = list(stream_core_agent(session, "Hi"))
            checks.append(("partial tokens streamed", [event.get("partial") for event in events if "partial" in event]
                           == ["Hello", "Hello traveler"]))
            checks.append(("stream completes", events[-1].get("done") and events[-1]["answer"] == "Hello traveler"))
            deleted = delete_all_user_data(user)
            with session_memory._get_conn() as conn:
                count = conn.execute("SELECT COUNT(*) FROM feedback WHERE user_id = ?", (user,)).fetchone()[0]
            checks.append(("feedback erased with user", deleted.get("deleted") and count == 0))
            for label, passed in checks:
                print(f"{'PASS' if passed else 'FAIL'}: {label}")
            return 0 if all(passed for _, passed in checks) else 1
        finally:
            session_memory.DB_PATH, cache.CACHE_PATH = old_db, old_cache


if __name__ == "__main__":
    raise SystemExit(main())
