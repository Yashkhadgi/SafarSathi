"""Offline smoke checks for language routing and session preference behavior."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.language_agent import (
    detect_language,
    input_normalizer,
    output_localizer,
    run_language_pipeline,
)
from memory import session_memory
from memory.language_preferences import get_session_preferences, save_session_preferences


def main():
    checks = []
    checks.append(("Hindi script", detect_language("मुझे जयपुर के बारे में बताइए") == "hi-IN"))
    checks.append(("Marathi script", detect_language("मला मदत हवी आहे") == "mr-IN"))
    checks.append(("Tamil script", detect_language("சென்னையில் என்ன பார்க்கலாம்") == "ta-IN"))
    checks.append(("Bengali script", detect_language("কলকাতায় কী দেখব") == "bn-IN"))
    checks.append(("Hinglish", detect_language("Goa me kya kya dekhna chahiye?") == "hinglish"))
    checks.append(("UI override", detect_language("What should I see?", "ta-IN") == "ta-IN"))

    with patch(
        "tools.translation_tool.translate_text",
        side_effect=["Where can I get help?", "आप 112 पर कॉल कर सकते हैं।"],
    ):
        normalized, detected = run_language_pipeline(
            "मुझे मदद चाहिए", lambda text: (checks.append(("normalized before core", text == "Where can I get help?")) or "You can call 112."),
            preference="auto",
        )
    checks.append(("pipeline localizes final output", normalized == "आप 112 पर कॉल कर सकते हैं।" and detected == "hi-IN"))

    with patch("tools.translation_tool.translate_text", side_effect=lambda text, **kwargs: text), patch(
        "agents.language_agent._claude_translate", return_value="Where is the railway station?"
    ):
        checks.append(("Claude fallback used", input_normalizer("रेलवे स्टेशन कहाँ है?", "hi-IN") == "Where is the railway station?"))

    with patch("tools.translation_tool.translate_text", return_value="ZXQKEEPURL0TOKENQXZ नमस्ते"):
        localized = output_localizer("Hello https://example.test/help", "hi-IN")
    checks.append(("URL survives localization", "https://example.test/help" in localized))
    checks.append(("English toggle preserves original", output_localizer("नमस्ते", "hi-IN", show_english=True) == "नमस्ते"))

    with patch("agents.language_agent._llm_language_guess", return_value="en-IN"), patch(
        "tools.translation_tool.translate_text", return_value="आपकी मदद कर सकता हूँ।"
    ):
        stable_reply, stable_language = run_language_pipeline(
            "Thanks, and what about food?", lambda _: "I can help with that.", previous_language="hi-IN"
        )
    checks.append(("short mixed-language follow-up stays stable", stable_language == "hi-IN" and stable_reply == "आपकी मदद कर सकता हूँ।"))

    with patch("tools.translation_tool.translate_text", side_effect=RuntimeError("offline")), patch(
        "agents.language_agent._claude_translate", return_value=""
    ):
        original = "தமிழில் கேள்வி https://example.test"
        checks.append(("normalizer failure preserves original", input_normalizer(original, "ta-IN") == original))
        checks.append(("localizer failure preserves original", output_localizer(original, "ta-IN") == original))

    original_db = session_memory.DB_PATH
    with tempfile.TemporaryDirectory() as directory:
        session_memory.DB_PATH = str(Path(directory) / "sessions.db")
        try:
            session_memory.create_session("language-smoke")
            session_id = session_memory.list_user_sessions("language-smoke")[0]["session_id"]
            persisted = save_session_preferences(session_id, language_code="bn-IN", show_english=True)
            prefs = get_session_preferences(session_id)
            checks.append(("session preference persists", persisted and prefs["language_code"] == "bn-IN" and prefs["show_english"]))
        finally:
            session_memory.DB_PATH = original_db

    phrase_path = Path(__file__).resolve().parents[1] / "data" / "emergency" / "phrases.json"
    phrases = json.loads(phrase_path.read_text(encoding="utf-8"))["phrases"]
    expected_codes = {"en-IN", "hi-IN", "bn-IN", "ta-IN", "te-IN", "mr-IN", "gu-IN", "kn-IN"}
    checks.append(("eight static SOS phrases", {item["code"] for item in phrases} == expected_codes))

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} {label}")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
