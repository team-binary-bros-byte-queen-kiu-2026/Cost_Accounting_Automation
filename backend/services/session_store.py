"""
In-memory session store.
Maps session_id → message history (trimmed to system + last 40 messages).
"""
from collections import defaultdict
from datetime import datetime

MAX_MESSAGES = 40  # system prompt + last 40 messages (20 turns)

_store: dict[str, dict] = defaultdict(lambda: {"messages": [], "estimate": None, "created_at": datetime.utcnow().isoformat()})


def get_history(session_id: str) -> list[dict]:
    return _store[session_id]["messages"]


def append_message(session_id: str, role: str, content: str):
    history = _store[session_id]["messages"]
    history.append({"role": role, "content": content})
    # Trim: keep system prompt (index 0) + last MAX_MESSAGES
    if len(history) > MAX_MESSAGES + 1:
        system = [m for m in history if m["role"] == "system"]
        non_system = [m for m in history if m["role"] != "system"][-MAX_MESSAGES:]
        _store[session_id]["messages"] = system + non_system


def set_estimate(session_id: str, estimate: dict):
    _store[session_id]["estimate"] = estimate


def get_estimate(session_id: str) -> dict | None:
    return _store[session_id].get("estimate")


def init_session(session_id: str, system_prompt: str):
    if not _store[session_id]["messages"]:
        _store[session_id]["messages"] = [{"role": "system", "content": system_prompt}]


def clear_session(session_id: str):
    del _store[session_id]


def list_sessions() -> list[str]:
    return list(_store.keys())
