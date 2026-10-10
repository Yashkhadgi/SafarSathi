"""Voice API endpoints: Transcribe (STT) and Speak (TTS) via Sarvam / Bhashini proxy."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
from backend.app.api.deps import get_current_user
from backend.app.db.models.user import User

router = APIRouter(prefix="/voice", tags=["voice"])


class SpeakRequest(BaseModel):
    text: str
    target_language_code: Optional[str] = "hi-IN"
    speaker_gender: Optional[str] = "female"


@router.post("/transcribe")
async def transcribe_audio(
    file: Optional[UploadFile] = File(default=None),
    language_code: Optional[str] = Form(default="hi-IN"),
    current_user: User = Depends(get_current_user),
):
    """Transcribe spoken audio via Sarvam/Bhashini voice tool wrapper."""
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file required.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio file.")

    try:
        from tools.voice_tool import transcribe_audio_payload
        ext = "webm"
        if file.filename and "." in file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower()
        elif file.content_type:
            if "mp4" in file.content_type or "m4a" in file.content_type:
                ext = "m4a"
            elif "wav" in file.content_type:
                ext = "wav"
            elif "ogg" in file.content_type:
                ext = "ogg"
        result = transcribe_audio_payload(content, file_format=ext, language_code=language_code)
        return result
    except ImportError:
        return {
            "transcript": "",
            "language_code": language_code,
            "simulated": True,
            "success": False,
        }
    except Exception as exc:
        return {"transcript": "", "error": f"Transcription failed: {exc}", "success": False}


@router.post("/speak")
def text_to_speech(
    req: SpeakRequest,
    current_user: User = Depends(get_current_user),
):
    """Synthesize text into spoken audio."""
    if not req.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text required.")

    try:
        from tools.voice_tool import synthesize_speech_payload
        result = synthesize_speech_payload(
            text=req.text.strip(),
            target_language_code=req.target_language_code or "hi-IN",
        )
        return result
    except ImportError:
        return {
            "audio_url": None,
            "message": "TTS synthesis service not configured.",
            "simulated": True,
        }
    except Exception as exc:
        return {"error": f"TTS synthesis failed: {exc}"}
