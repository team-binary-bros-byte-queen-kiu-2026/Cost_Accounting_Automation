"""GET /health — returns {"status":"ok"} in <500ms. No LLM call. Required for Week 15."""
from fastapi import APIRouter
from ..services.episode_log import count_entries

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "construct-ai-backend",
        "episode_log_entries": count_entries(),
    }
