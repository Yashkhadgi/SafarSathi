import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64
import io
import requests
from config.settings import SARVAM_API_KEY

BASE_URL = "https://api.sarvam.ai"

# Valid speakers for bulbul:v3
# Female: ritu, priya, neha, pooja, simran, kavya, ishita, shreya, roopa, kavitha, shruti, suhani, rupali, tanya, mani
# Male: aditya, ashutosh, rahul, rohan, amit, dev, varun, manan, sumit, kabir, aayan, shubh, advait, anand, tarun, sunny, gokul, vijay, mohit, rehan, soham
DEFAULT_SPEAKER_EN = "advait"    # English
DEFAULT_SPEAKER_HI = "advait"    # Hindi


def speech_to_text(audio_bytes: bytes, file_format: str = "wav", lang_code: str = "hi-IN") -> str:
    """
    Converts audio bytes → text transcript via Sarvam STT (saaras:v2).
    Returns transcript string, or "" on failure. NEVER raises.
    """
    try:
        if not SARVAM_API_KEY:
            print("Sarvam STT skipped: SARVAM_API_KEY not set.")
            return ""

        mime_map = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "ogg": "audio/ogg",
            "webm": "audio/webm",
            "flac": "audio/flac",
            "m4a": "audio/mp4",
        }
        mime = mime_map.get(file_format.lower(), "audio/wav")

        files = {"file": (f"audio.{file_format}", io.BytesIO(audio_bytes), mime)}
        data = {
            "model": "saaras:v3",
            "language_code": lang_code,
        }

        resp = requests.post(
            f"{BASE_URL}/speech-to-text",
            headers={"api-subscription-key": SARVAM_API_KEY.strip()},
            files=files,
            data=data,
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        return result.get("transcript", "").strip()

    except Exception as e:
        print(f"Sarvam STT failed: {e}")
        return ""


def text_to_speech(text: str, lang_code: str = "en-IN", speaker: str = DEFAULT_SPEAKER_EN) -> bytes:
    """
    Converts text → audio bytes (WAV/PCM) via Sarvam TTS (bulbul:v3).
    Long text is chunked at sentence boundaries (500 char limit per call).
    Returns raw audio bytes, or b"" on failure. NEVER raises.
    """
    try:
        if not SARVAM_API_KEY:
            print("Sarvam TTS skipped: SARVAM_API_KEY not set.")
            return b""

        chunks = _chunk_text(text, max_chars=500)
        audio_parts = []

        for chunk in chunks:
            if not chunk.strip():
                continue
            payload = {
                "inputs": [chunk],
                "target_language_code": lang_code,
                "speaker": speaker,
                "pace": 1.0,
                "model": "bulbul:v3",
            }
            resp = requests.post(
                f"{BASE_URL}/text-to-speech",
                headers={
                    "api-subscription-key": SARVAM_API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            audios = data.get("audios", [])
            if audios:
                audio_parts.append(base64.b64decode(audios[0]))

        if not audio_parts:
            return b""

        return b"".join(audio_parts)

    except Exception as e:
        print(f"Sarvam TTS failed: {e}")
        return b""


def _chunk_text(text: str, max_chars: int = 500) -> list:
    """Split text into sentence-aware chunks under max_chars."""
    # Strip markdown formatting (bold, headers, bullets) for cleaner TTS
    import re
    text = re.sub(r'\*+', '', text)          # remove ** bold
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # remove # headers
    text = re.sub(r'^\s*[-•✓✗]\s*', '', text, flags=re.MULTILINE)  # remove bullets
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # remove markdown links
    text = re.sub(r'\n{2,}', '. ', text)     # double newlines → sentence break
    text = re.sub(r'\n', ' ', text)           # single newlines → space
    text = re.sub(r'\s+', ' ', text).strip()

    if len(text) <= max_chars:
        return [text]

    chunks = []
    sentences = re.split(r'(?<=[.!?])\s+', text)

    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk = (current_chunk + " " + sentence).strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if len(sentence) > max_chars:
                for i in range(0, len(sentence), max_chars):
                    chunks.append(sentence[i:i + max_chars])
                current_chunk = ""
            else:
                current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk)

    return chunks if chunks else [text[:max_chars]]


if __name__ == "__main__":
    print("=== Testing TTS (English) ===")
    audio = text_to_speech(
        "Hello! I am your multilingual tourist assistant. I can help you plan trips, find local information, and handle emergencies.",
        lang_code="en-IN",
        speaker=DEFAULT_SPEAKER_EN,
    )
    if audio:
        with open("/tmp/test_tts_en.wav", "wb") as f:
            f.write(audio)
        print(f"TTS EN OK: {len(audio)} bytes → /tmp/test_tts_en.wav")
    else:
        print("TTS EN: Failed")

    print("\n=== Testing TTS (Hindi) ===")
    audio_hi = text_to_speech(
        "नमस्ते! मैं आपका बहुभाषी पर्यटन सहायक हूं। मैं आपकी यात्रा की योजना बनाने में मदद कर सकता हूं।",
        lang_code="hi-IN",
        speaker=DEFAULT_SPEAKER_HI,
    )
    if audio_hi:
        with open("/tmp/test_tts_hi.wav", "wb") as f:
            f.write(audio_hi)
        print(f"TTS HI OK: {len(audio_hi)} bytes → /tmp/test_tts_hi.wav")
    else:
        print("TTS HI: Failed")

    print("\nSTT: function ready — needs real audio bytes to test")
