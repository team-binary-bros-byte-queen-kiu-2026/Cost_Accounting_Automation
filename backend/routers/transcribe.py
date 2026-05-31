"""
POST /transcribe — Speech-to-Text (HW2 STT requirement).
Accepts MP3 or WAV, returns transcript via OpenRouter/Whisper-1.
"""
import os
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from ..services.rate_limiter import check_rate_limit

router = APIRouter()
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

ALLOWED_AUDIO = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/wave", "audio/x-wav"}
MAX_AUDIO_MB = 25


@router.post("/transcribe")
async def transcribe(request: Request, file: UploadFile = File(...)):
    check_rate_limit(request, "transcribe")

    audio_bytes = await file.read()
    if len(audio_bytes) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Audio file must be under {MAX_AUDIO_MB}MB.")

    try:
        resp = httpx.post(
            "https://openrouter.ai/api/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            files={"file": (file.filename or "audio.mp3", audio_bytes, file.content_type or "audio/mpeg")},
            data={"model": "openai/whisper-1"},
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return {"transcript": data.get("text", ""), "duration": data.get("duration")}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"STT service error: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
