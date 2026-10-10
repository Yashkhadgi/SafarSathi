"""Failure-safe two-way voice conversation handler."""

import os
import hashlib
import shutil
import time
import uuid
from pathlib import Path

from agents.language_agent import _claude_translate, detect_language
from tools.translation_tool import translate_text
from tools.voice_tool import speech_to_text, text_to_speech


AUDIO_ROOT = Path(__file__).resolve().parents[1] / "memory" / "live_audio"


def _user_audio_dir(user_id):
    return AUDIO_ROOT / hashlib.sha256(str(user_id).encode("utf-8")).hexdigest()


def delete_user_audio(user_id):
    try:
        shutil.rmtree(_user_audio_dir(user_id), ignore_errors=False)
        return {"deleted": True}
    except FileNotFoundError:
        return {"deleted": True}
    except Exception as exc:
        return {"error": str(exc)}


def translate_turn(audio_path, typed_text, speaker, language_a, language_b, history,
                   user_id="anonymous"):
    """Return a structured turn and updated in-browser history; never raise."""
    try:
        turns = list(history or [])
        if speaker not in ("A", "B"):
            return {"error": "Choose speaker A or B", "history": turns}
        resolved_a = next((turn["detected_language"] for turn in turns
                           if turn["speaker"] == "A" and turn.get("detected_language")), None)
        source = ("unknown" if language_a == "auto" else language_a) if speaker == "A" else language_b
        target = language_b if speaker == "A" else (resolved_a or language_a)
        if target == "auto":
            return {"error": "Let speaker A speak first so their language can be detected", "history": turns}
        started = time.monotonic()
        transcript = str(typed_text or "").strip()
        if not transcript and audio_path:
            with open(audio_path, "rb") as audio_file:
                contents = audio_file.read()
            if not contents:
                return {"error": "Audio recording is empty; try again or type the words", "history": turns}
            extension = os.path.splitext(audio_path)[1].lstrip(".") or "wav"
            transcript = speech_to_text(contents, file_format=extension, lang_code=source)
        if not transcript:
            return {"error": "Could not understand the audio; try again or type the words", "history": turns}
        detected = detect_language(transcript) if source == "unknown" else source
        translated = translate_text(transcript, target_lang_code=target, source_lang_code=detected)
        translation_available = bool(translated and (translated != transcript or detected == target))
        if not translation_available and detected != target:
            fallback = _claude_translate(transcript, target)
            if fallback:
                translated = fallback
                translation_available = True
        if not translation_available:
            translated = transcript
        audio_file_path = None
        if translation_available:
            audio = text_to_speech(translated, lang_code=target)
            if audio:
                output_dir = _user_audio_dir(user_id)
                output_dir.mkdir(parents=True, exist_ok=True)
                audio_file_path = str(output_dir / f"{uuid.uuid4().hex}.wav")
                Path(audio_file_path).write_bytes(audio)
        turn = {"speaker": speaker, "original": transcript, "translated": translated,
                "detected_language": detected, "target_language": target,
                "audio_path": audio_file_path,
                "status": ("Translation ready" if audio_file_path else
                           "Text-only translation; speech unavailable" if translation_available else
                           "Translation unavailable; showing original text"),
                "latency_seconds": round(time.monotonic() - started, 2)}
        turns.append(turn)
        return {"turn": turn, "history": turns}
    except Exception as exc:
        return {"error": f"Live translation unavailable: {exc}", "history": list(history or [])}
