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
        result = transcribe_audio_payload(content, language_code=language_code)
        return result
    except ImportError:
        # Fallback simulator when voice model is not configured locally
        return {
            "transcript": "Audio received. Voice STT service not configured.",
            "language_code": language_code,
            "simulated": True,
        }
    except Exception as exc:
        return {"error": f"Transcription failed: {exc}"}


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
