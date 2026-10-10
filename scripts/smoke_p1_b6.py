"""Offline checks for language labels, static phrases, and cached audio."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.language_agent import detect_language
from tools.phrasebook import emergency_phrase, phrase_for


def check(label, ok):
    print(f"{'PASS' if ok else 'FAIL'} {label}")
    return bool(ok)


def main():
    samples = {
        "hi-IN": "मुझे मदद चाहिए", "bn-IN": "আমার সাহায্য দরকার",
        "ta-IN": "எனக்கு உதவி தேவை", "te-IN": "నాకు సహాయం కావాలి",
        "mr-IN": "मला मदत पाहिजे", "gu-IN": "મને મદદ જોઈએ છે",
        "kn-IN": "ನನಗೆ ಸಹಾಯ ಬೇಕು", "en-IN": "I need help",
        "hinglish": "mujhe madad chahiye",
    }
    passed = [check(f"detect {code}", detect_language(text) == code)
              for code, text in samples.items()]
    for language in ("en-IN", "hi-IN", "bn-IN", "ta-IN", "te-IN", "mr-IN", "gu-IN", "kn-IN"):
        emergency = emergency_phrase(language)
        passed.append(check(f"emergency text {language}", bool(emergency.get("text"))))
        for situation in ("restaurant", "taxi", "hotel", "bargaining", "hospital", "directions"):
            phrase = phrase_for(situation, language)
            passed.append(check(f"phrase {situation}/{language}",
                                bool(phrase.get("text") and phrase.get("pronunciation"))))
    audio_count = sum(bool(emergency_phrase(code).get("audio_path")) for code in samples if code != "hinglish")
    print(f"INFO offline emergency audio: {audio_count}/8 languages")
    return 0 if all(passed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
