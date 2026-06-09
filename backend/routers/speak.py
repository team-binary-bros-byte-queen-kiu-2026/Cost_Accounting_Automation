"""
POST /speak — Text-to-Speech (HW2 TTS requirement).
Converts estimate summary or any text to MP3 audio via OpenRouter/OpenAI tts-1.
"""
import os
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from ..services.rate_limiter import check_rate_limit

router = APIRouter()
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

AVAILABLE_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]


class SpeakRequest(BaseModel):
    text: str
    voice: str = "nova"   # default voice


@router.post("/speak")
async def speak(request: Request, body: SpeakRequest):
    check_rate_limit(request, "speak")

    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    if len(body.text) > 4096:
        raise HTTPException(status_code=400, detail="Text too long (max 4096 characters).")

    if body.voice not in AVAILABLE_VOICES:
        raise HTTPException(status_code=400, detail=f"Voice must be one of: {AVAILABLE_VOICES}")

    try:
        resp = httpx.post(
            "https://openrouter.ai/api/v1/audio/speech",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/tts-1",
                "input": body.text,
                "voice": body.voice,
                "data_collection": "deny",
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        return Response(content=resp.content, media_type="audio/mpeg")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"TTS service error: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")
