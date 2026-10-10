"""Static situation phrases and cached audio without requiring live APIs."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHRASES_PATH = ROOT / "data" / "phrasebook" / "phrases.json"
EMERGENCY_PATH = ROOT / "data" / "emergency" / "phrases.json"
AUDIO_DIR = ROOT / "data" / "phrasebook" / "audio"


def phrase_for(situation, language):
    try:
        data = json.loads(PHRASES_PATH.read_text(encoding="utf-8"))
        entry = data["situations"][situation][language]
        audio = AUDIO_DIR / f"{situation}_{language}.wav"
        return {"situation": situation, "language": language,
                "text": entry[0], "pronunciation": entry[1],
                "review_status": data["review_status"],
                "audio_path": str(audio) if audio.is_file() else None}
    except Exception as exc:
        return {"error": f"Phrase unavailable: {exc}"}


def emergency_phrase(language):
    try:
        data = json.loads(EMERGENCY_PATH.read_text(encoding="utf-8"))
        item = next((row for row in data["phrases"] if row["code"] == language), None)
        if not item:
            return {"error": "Emergency phrase unavailable"}
        audio = AUDIO_DIR / f"emergency_{language}.wav"
        return {"language": item["language"], "text": item["text"],
                "audio_path": str(audio) if audio.is_file() else None}
    except Exception as exc:
        return {"error": f"Emergency phrase unavailable: {exc}"}


def get_all_phrases():
    try:
        return json.loads(PHRASES_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"error": str(exc)}


def get_all_emergency_phrases():
    try:
        return json.loads(EMERGENCY_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"error": str(exc)}

