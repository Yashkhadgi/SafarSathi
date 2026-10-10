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
        situations = data.get("situations", {})

        sit_key = str(situation or "").strip().lower()
        if sit_key not in situations:
            # Match aliases
            if any(k in sit_key for k in ["food", "eat", "veg", "dinner", "lunch"]):
                sit_key = "restaurant"
            elif any(k in sit_key for k in ["cab", "auto", "car", "ride"]):
                sit_key = "taxi"
            elif any(k in sit_key for k in ["room", "stay", "lodge"]):
                sit_key = "hotel"
            elif any(k in sit_key for k in ["price", "cost", "shop", "discount", "cheap"]):
                sit_key = "bargaining"
            elif any(k in sit_key for k in ["doctor", "med", "sick", "ill"]):
                sit_key = "hospital"
            else:
                sit_key = next(iter(situations.keys()))

        lang_key = str(language or "").strip().lower()
        lang_map = {
            "hi": "hi-IN", "hindi": "hi-IN",
            "en": "en-IN", "english": "en-IN",
            "bn": "bn-IN", "bengali": "bn-IN",
            "ta": "ta-IN", "tamil": "ta-IN",
            "te": "te-IN", "telugu": "te-IN",
            "mr": "mr-IN", "marathi": "mr-IN",
            "gu": "gu-IN", "gujarati": "gu-IN",
            "kn": "kn-IN", "kannada": "kn-IN",
        }
        lang_code = lang_map.get(lang_key, lang_key if "-" in lang_key else "hi-IN")

        entry = situations[sit_key].get(lang_code) or situations[sit_key].get("hi-IN") or ["", ""]
        audio = AUDIO_DIR / f"{sit_key}_{lang_code}.wav"
        res = {"situation": sit_key, "language": lang_code,
               "text": entry[0], "pronunciation": entry[1],
               "review_status": data.get("review_status", "verified"),
               "audio_path": str(audio) if audio.is_file() else None}
        res["ui"] = {
            "type": "phrasebook",
            "version": "1.0",
            "data": {
                "language": lang_code,
                "phrases": [
                    {
                        "situation": sit_key.replace("_", " ").title(),
                        "english": sit_key.replace("_", " ").title(),
                        "translated": entry[0],
                        "phonetic": entry[1],
                        "audio_sample_url": f"/api/v1/phrasebook/audio/{sit_key}_{lang_code}.wav" if audio.is_file() else None,
                    }
                ]
            }
        }
        return res
    except Exception as exc:
        return {"error": f"Phrase unavailable: {exc}"}



def emergency_phrase(language):
    try:
        data = json.loads(EMERGENCY_PATH.read_text(encoding="utf-8"))
        item = next((row for row in data["phrases"] if row["code"] == language), None)
        if not item:
            return {"error": "Emergency phrase unavailable"}
        audio = AUDIO_DIR / f"emergency_{language}.wav"
        res = {"language": item["language"], "text": item["text"],
               "audio_path": str(audio) if audio.is_file() else None}
        res["ui"] = {
            "type": "phrasebook",
            "version": "1.0",
            "data": {
                "language": item["language"],
                "phrases": [
                    {
                        "situation": "Emergency Help",
                        "english": "Please help me, it's an emergency!",
                        "translated": item["text"],
                        "phonetic": item.get("phonetic", item["text"]),
                        "audio_sample_url": f"/api/v1/phrasebook/audio/emergency_{language}.wav" if audio.is_file() else None,
                    }
                ]
            }
        }
        return res
    except Exception as exc:
        return {"error": f"Emergency phrase unavailable: {exc}"}


def get_all_phrases():
    try:
        data = json.loads(PHRASES_PATH.read_text(encoding="utf-8"))
        # Format phrases for UI
        phrases_list = []
        situations = data.get("situations", {})
        for sit_key, lang_map in situations.items():
            for lang_code, vals in lang_map.items():
                audio = AUDIO_DIR / f"{sit_key}_{lang_code}.wav"
                phrases_list.append({
                    "situation": sit_key.replace("_", " ").title(),
                    "language": lang_code,
                    "english": sit_key.replace("_", " ").title(),
                    "translated": vals[0] if len(vals) > 0 else "",
                    "phonetic": vals[1] if len(vals) > 1 else "",
                    "audio_sample_url": f"/api/v1/phrasebook/audio/{sit_key}_{lang_code}.wav" if audio.is_file() else None,
                })
        data["ui"] = {
            "type": "phrasebook",
            "version": "1.0",
            "data": {
                "language": "All Languages",
                "phrases": phrases_list[:20],
            }
        }
        return data
    except Exception as exc:
        return {"error": str(exc)}


def get_all_emergency_phrases():
    try:
        data = json.loads(EMERGENCY_PATH.read_text(encoding="utf-8"))
        phrases_list = []
        for item in data.get("phrases", []):
            audio = AUDIO_DIR / f"emergency_{item.get('code')}.wav"
            phrases_list.append({
                "situation": "Emergency",
                "language": item.get("language"),
                "english": "Emergency Assistance",
                "translated": item.get("text"),
                "phonetic": item.get("phonetic", item.get("text")),
                "audio_sample_url": f"/api/v1/phrasebook/audio/emergency_{item.get('code')}.wav" if audio.is_file() else None,
            })
        data["ui"] = {
            "type": "phrasebook",
            "version": "1.0",
            "data": {
                "language": "Emergency All",
                "phrases": phrases_list,
            }
        }
        return data
    except Exception as exc:
        return {"error": str(exc)}


