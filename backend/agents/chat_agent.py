"""
Chat specialist agent.
Handles follow-up questions about the cost estimate using session memory + RAG.
"""
import json
from ..services import openrouter, session_store, rag

# ── Large system prompt (>1024 tokens) — cached on first call ─────────────
SYSTEM_PROMPT_TEMPLATE = """You are ConstructAI, an expert construction cost estimation assistant for the Georgian market.

You help users understand and refine cost estimates for building projects. You have access to:
1. The current project estimate (provided below)
2. A knowledge base of Georgian construction prices, material specifications, and labor rates
3. Regional construction guides for Tbilisi and wider Georgia

CURRENT PROJECT ESTIMATE:
{estimate_json}

RETRIEVED KNOWLEDGE:
{rag_context}

GUIDELINES:
- Keep answers SHORT — 2 to 4 sentences maximum. Be direct and specific.
- For calculations, show the key number only (e.g. "18 m³ × 195 GEL = 3,510 GEL").
- Always include the currency (GEL) in cost figures.
- For "what if" scenarios, state the cost difference only — skip lengthy explanations.
- If something is outside the estimate, say so in one sentence.
- Never add disclaimers about getting quotes unless the user asks.

IMPORTANT: You cannot access external information beyond what is provided above.
If asked about prices not in the database, say so in one sentence.
"""


def build_system_prompt(session_id: str) -> str:
    estimate = session_store.get_estimate(session_id)
    estimate_json = json.dumps(estimate, indent=2, ensure_ascii=False) if estimate else "No estimate available yet."
    # RAG: retrieve relevant context for this session
    rag_chunks = rag.retrieve(f"construction cost estimate {estimate.get('building_type', '')} Georgia", top_k=3) if estimate else []
    rag_context = rag.format_context(rag_chunks) or "No additional knowledge retrieved."
    return SYSTEM_PROMPT_TEMPLATE.format(
        estimate_json=estimate_json,
        rag_context=rag_context,
    )


def get_chat_response(session_id: str, user_message: str) -> dict:
    """Non-streaming chat response for programmatic use."""
    system_prompt = build_system_prompt(session_id)
    session_store.init_session(session_id, system_prompt)
    session_store.append_message(session_id, "user", user_message)

    history = session_store.get_history(session_id)
    result = openrouter.chat_with_fallback(
        messages=history,
        session_id=session_id,
    )
    session_store.append_message(session_id, "assistant", result["content"])
    return result


def get_chat_stream(session_id: str, user_message: str):
    """Generator yielding SSE chunks for streaming response."""
    system_prompt = build_system_prompt(session_id)
    session_store.init_session(session_id, system_prompt)
    session_store.append_message(session_id, "user", user_message)

    history = session_store.get_history(session_id)
    full_response = ""

    for chunk in openrouter.stream_chat(messages=history, session_id=session_id):
        if chunk.startswith("data: {"):
            try:
                import json as _json
                token = _json.loads(chunk[6:]).get("token", "")
                full_response += token
            except Exception:
                pass
        yield chunk

    # Save complete assistant response to history
    if full_response:
        session_store.append_message(session_id, "assistant", full_response)
