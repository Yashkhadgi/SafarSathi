"""Generate offline phrase audio with Sarvam or installed macOS voices.

Missing voices are reported explicitly. Existing audio is never replaced.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.phrasebook import AUDIO_DIR, EMERGENCY_PATH, PHRASES_PATH


MAC_VOICES = {
    "en-IN": "Aman", "hi-IN": "Lekha", "bn-IN": "Piya",
    "ta-IN": "Vani", "te-IN": "Geeta", "kn-IN": "Soumya",
}


def _sarvam_audio(text, language):
    try:
        from config.settings import SARVAM_API_KEY
        if not SARVAM_API_KEY:
            return b""
        from tools.voice_tool import text_to_speech
        return text_to_speech(text, lang_code=language)
    except Exception:
        return b""


def _mac_audio(text, language, destination):
    if not (shutil.which("say") and shutil.which("afconvert") and language in MAC_VOICES):
        return False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            aiff = Path(tmp) / "spoken.aiff"
            subprocess.run(["say", "-v", MAC_VOICES[language], "-o", str(aiff), text],
                           check=True, timeout=30, capture_output=True)
            subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", str(aiff),
                            "-o", str(destination)], check=True, timeout=30,
                           capture_output=True)
        return destination.is_file() and destination.stat().st_size > 44
    except Exception:
        destination.unlink(missing_ok=True)
        return False


def _generate(name, language, text):
    destination = AUDIO_DIR / f"{name}_{language}.wav"
    if destination.is_file():
        return "cached"
    if _mac_audio(text, language, destination):
        return "generated"
    audio = _sarvam_audio(text, language)
    if audio:
        destination.write_bytes(audio)
        return "generated"
    return "unavailable"


def main():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(PHRASES_PATH.read_text(encoding="utf-8"))
    emergency = json.loads(EMERGENCY_PATH.read_text(encoding="utf-8"))
    counts = {"generated": 0, "cached": 0, "unavailable": 0}
    for item in emergency["phrases"]:
        outcome = _generate("emergency", item["code"], item["text"])
        counts[outcome] += 1
        print(f"{outcome}: emergency {item['code']}")
    for situation, translations in data["situations"].items():
        for language, pair in translations.items():
            outcome = _generate(situation, language, pair[0])
            counts[outcome] += 1
            print(f"{outcome}: {situation} {language}")
    print(counts)
    return 0 if counts["generated"] + counts["cached"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
