# Agent Architecture — Lab 7

**Pattern:** Orchestrator / Specialist (LangGraph)

---

## Overview

Every `/analyze` request runs through a compiled LangGraph `StateGraph`. The orchestrator graph sequences two specialist agents and routes conditionally based on the output.

```
POST /analyze
     │
     ▼
 VisionAgent          → identifies building components from image
     │
     ▼
 EstimationAgent      → prices each component, computes grand total
     │
     ▼
 [grand_total > 500k GEL?]
     │ YES                  NO
     ▼                       ▼
 HumanReviewNode          END
     │
     ▼
    END
```

Follow-up chat is handled by a separate `ChatAgent` that is not part of the LangGraph pipeline — it runs per-message with session memory and RAG context.

---

## AgentState

Defined in `backend/agents/state.py`. All inter-agent communication passes through this typed dict — no global state, no side channels.

```python
class AgentState(TypedDict):
    session_id: str
    user_request: str
    image_path: Optional[str]
    image_base64: Optional[str]
    message_history: list[dict]
    current_step: str           # "vision" | "estimation" | "done" | "needs_review"
    approval_required: bool     # True when grand_total_gel > 500,000
    approval_granted: bool
    retry_count: int
    timeout_ms: int
    identified_components: Optional[dict]
    cost_estimate: Optional[dict]
    model_used: str
    fallback_triggered: bool
    cache_read_tokens: int
    cache_write_tokens: int
    latency_ms: int
    error: Optional[str]
```

Every node receives the full state and returns an updated copy. Nodes never mutate state in place.

---

## Specialist Agents

### VisionAgent (`backend/agents/vision_agent.py`)

- **Input:** `image_base64`
- **Action:** Sends image to OpenRouter (`gemini-2.5-flash` by default). Parses the JSON response into `identified_components`.
- **Output:** Sets `identified_components`, `model_used`, `fallback_triggered`, `cache_read_tokens`, `latency_ms`
- **Fallback:** On 429 or 5xx, advances to `claude-3-5-haiku` then `gpt-4o-mini`

### EstimationAgent (`backend/agents/estimation_agent.py`)

- **Input:** `identified_components`
- **Action:** For each component, looks up unit price from SQLite DB (also logged as an MCP tool call). Multiplies quantity × price. Adds 35% labor estimate.
- **Output:** Sets `cost_estimate` (itemized line items + `grand_total_gel`), `approval_required`
- **Guard:** If `grand_total_gel > 500,000 GEL`, sets `approval_required = True` and routes to `human_review`

### HumanReviewNode (`backend/agents/graph.py`)

- Placeholder for human-in-the-loop. In production: would send notification and await approval.
- In current demo: auto-approves but appends a warning note to the estimate.
- Sets `approval_granted = True`.

### ChatAgent (`backend/agents/chat_agent.py`)

- Runs outside the LangGraph pipeline, invoked per chat turn.
- Loads estimate from `SessionStore`, retrieves top-3 RAG chunks from ChromaDB, injects both into the system prompt.
- Streams response via OpenRouter (`claude-3-5-haiku`).
- Appends full assistant reply to session history after streaming completes.
- Trims history to last 20 turns to control token cost.

---

## Irreversible Actions and Guards

| Action | Irreversible? | Guard |
|---|---|---|
| POST image to OpenRouter | No — read-only API call | None needed |
| Append to `episode-log.jsonl` | No — append-only, never overwritten | None needed |
| Update material price in DB | **Yes** — overwrites old price | Admin must confirm via `PUT /admin/materials/{id}/price` |
| Estimate > 500,000 GEL delivered to client | **High-stakes** financial output | `approval_required = True` in AgentState; blocked until `approval_granted = True` |
| TTS/STT audio processing | No — in-memory only, never persisted | None needed |

---

## Graph Definition

```python
# backend/agents/graph.py
workflow = StateGraph(AgentState)
workflow.add_node("vision", vision_node)
workflow.add_node("estimation", estimation_node)
workflow.add_node("human_review", human_review_node)

workflow.set_entry_point("vision")
workflow.add_edge("vision", "estimation")
workflow.add_conditional_edges(
    "estimation",
    should_request_approval,   # returns "done" or "needs_review"
    {"done": END, "needs_review": "human_review"},
)
workflow.add_edge("human_review", END)

estimation_graph = workflow.compile()
```
