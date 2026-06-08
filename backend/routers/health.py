"""GET /health — returns {"status":"ok"} in <500ms. No LLM call. Required for Week 15."""
import time
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()

START_TIME = time.time()
VERSION = "1.0.0"


@router.get("/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": VERSION,
    }
