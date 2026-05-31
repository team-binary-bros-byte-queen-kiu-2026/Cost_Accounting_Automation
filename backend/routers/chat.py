"""
POST /chat/stream — SSE streaming chat with session memory.
Lab 6 requirement: text/event-stream, first token <2s, [DONE] sentinel.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ..agents.chat_agent import get_chat_stream
from ..services.rate_limiter import check_rate_limit

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/chat/stream")
async def chat_stream(request: Request, body: ChatRequest):
    check_rate_limit(request, "chat")

    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    if len(body.message) > 2000:
        raise HTTPException(status_code=400, detail="Message too long (max 2000 characters).")

    def generate():
        try:
            for chunk in get_chat_stream(
                session_id=body.session_id,
                user_message=body.message,
            ):
                yield chunk
        except Exception as e:
            import json
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
