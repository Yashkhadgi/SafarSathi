import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from config.settings import SARVAM_API_KEY

BASE_URL = "https://api.sarvam.ai"


def translate_text(text: str, target_lang_code: str = "hi-IN", source_lang_code: str = "en-IN") -> str:
    """
    Translates text via Sarvam Translate. Returns translated text, or the
    ORIGINAL text unchanged on any failure (never raises, never returns
    empty — chat should still work even if translation is down).
    """
    try:
        if not SARVAM_API_KEY:
            print("Sarvam translate skipped: SARVAM_API_KEY not set.")
            return text
        resp = requests.post(
            f"{BASE_URL}/translate",
            headers={"api-subscription-key": SARVAM_API_KEY},
            json={
                "input": text,
                "source_language_code": source_lang_code,
                "target_language_code": target_lang_code,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("translated_text", text)
    except Exception as e:
        print(f"Sarvam translation failed: {e}")
        return text


if __name__ == "__main__":
    print(translate_text("Where is the nearest train station?", target_lang_code="hi-IN"))
