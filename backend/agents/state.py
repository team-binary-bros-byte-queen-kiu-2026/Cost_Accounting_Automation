"""
AgentState — typed dict used by LangGraph.
All fields required by Lab 7 checklist.
"""
from typing import TypedDict, Optional


class AgentState(TypedDict):
    session_id: str
    user_request: str
    image_path: Optional[str]
    image_base64: Optional[str]
    message_history: list[dict]
    current_step: str                  # "vision" | "estimation" | "done" | "needs_review"
    approval_required: bool            # True when estimate > 500,000 GEL
    approval_granted: bool
    retry_count: int
    timeout_ms: int
    identified_components: Optional[dict]   # output of vision agent
    cost_estimate: Optional[dict]           # output of estimation agent
    model_used: str
    fallback_triggered: bool
    cache_read_tokens: int
    cache_write_tokens: int
    latency_ms: int
    error: Optional[str]
