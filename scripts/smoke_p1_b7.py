"""Mocked two-way translation and key-free fallback checks."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.live_translation import translate_turn
from ui import live_translation


def check(label, ok):
    print(f"{'PASS' if ok else 'FAIL'} {label}")
    return bool(ok)


def main():
    passed = []
    with patch("ui.live_translation.translate_text", side_effect=["Hello", "नमस्ते"]), \
         patch("ui.live_translation.text_to_speech", return_value=b""):
        first = translate_turn(None, "नमस्ते", "A", "auto", "en-IN", [])
        second = translate_turn(None, "Hello", "B", "auto", "en-IN", first["history"])
    passed.append(check("auto A language", first["turn"]["detected_language"] == "hi-IN"))
    passed.append(check("two-way target", second["turn"]["target_language"] == "hi-IN"
                        and second["turn"]["translated"] == "नमस्ते"))
    passed.append(check("text-only fallback", first["turn"]["audio_path"] is None
                        and "Text-only" in first["turn"]["status"]))
    blocked = translate_turn(None, "Hello", "B", "auto", "en-IN", [])
    passed.append(check("A must speak first for auto pair", "error" in blocked))
    with patch("ui.live_translation.translate_text", return_value="नमस्ते"), \
         patch("ui.live_translation._claude_translate", return_value=""):
        failed = translate_turn(None, "नमस्ते", "A", "hi-IN", "ta-IN", [])
    passed.append(check("failed translation clearly labeled", "unavailable" in
                        failed["turn"]["status"].lower()))
    passed.append(check("noisy or missing audio message", "error" in translate_turn(
        None, "", "A", "hi-IN", "en-IN", [])))
    with tempfile.TemporaryDirectory() as tmp, \
         patch.object(live_translation, "AUDIO_ROOT", Path(tmp)), \
         patch("ui.live_translation.translate_text", return_value="Hello"), \
         patch("ui.live_translation.text_to_speech", return_value=b"RIFFtest"):
        voiced = translate_turn(None, "नमस्ते", "A", "hi-IN", "en-IN", [], user_id="alice")
        audio_path = Path(voiced["turn"]["audio_path"])
        passed.append(check("user-scoped audio exists", audio_path.is_file()))
        erased = live_translation.delete_user_audio("alice")
        passed.append(check("user audio delete", erased.get("deleted") and not audio_path.exists()))
    return 0 if all(passed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
