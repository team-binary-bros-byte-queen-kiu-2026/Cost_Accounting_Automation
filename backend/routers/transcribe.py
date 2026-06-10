"""
POST /transcribe — Speech-to-Text (HW2 STT requirement).
Accepts audio upload (webm, mp3, wav), returns transcript via OpenRouter Whisper.
"""
import base64
import os
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from ..services.rate_limiter import check_rate_limit

router = APIRouter()
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

MAX_AUDIO_MB = 25


def _audio_format(content_type: str | None, filename: str | None) -> str:
    ct = (content_type or "").lower()
    name = (filename or "").lower()
    if "webm" in ct or name.endswith(".webm"):
        return "webm"
    if "wav" in ct or name.endswith(".wav"):
        return "wav"
    if "mpeg" in ct or "mp3" in ct or name.endswith(".mp3"):
        return "mp3"
    if "ogg" in ct or name.endswith(".ogg"):
        return "ogg"
    if "mp4" in ct or name.endswith(".m4a"):
        return "m4a"
    return "webm"


@router.post("/transcribe")
async def transcribe(request: Request, file: UploadFile = File(...)):
    check_rate_limit(request, "transcribe")

    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "sk-or-your-key-here":
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY is not set. Add it to .env at the repo root.",
        )

    audio_bytes = await file.read()
    if len(audio_bytes) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Audio file must be under {MAX_AUDIO_MB}MB.")
    if len(audio_bytes) < 500:
        raise HTTPException(status_code=400, detail="Audio file too short.")

    fmt = _audio_format(file.content_type, file.filename)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    try:
        resp = httpx.post(
            "https://openrouter.ai/api/v1/audio/transcriptions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/whisper-1",
                "input_audio": {
                    "data": audio_b64,
                    "format": fmt,
                },
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "transcript": data.get("text", ""),
            "duration": data.get("usage", {}).get("seconds"),
        }
    except httpx.HTTPStatusError as e:
        detail = e.response.text[:200] if e.response.text else str(e.response.status_code)
        raise HTTPException(status_code=502, detail=f"STT service error: {detail}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
