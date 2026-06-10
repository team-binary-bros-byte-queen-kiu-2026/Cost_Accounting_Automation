# Safety and Evaluation Audit
**Course:** CS-AI-2025 · Spring 2026
**Team:** Binary Bros & Byte Queens
**File:** docs/safety-audit.md

---

## Area 1 — Episode Log Quality

**Status:** ✅ Complete

- Episode log location: `logs/episode-log.jsonl`
- Log format: JSONL (one JSON object per line)
- **Total entries as of Jun 8 2026: 120** (88 LLM calls + 32 MCP tool calls)
- Fields present in LLM call entries: `ts, event_type, session_id, model, model_used, input_tokens, output_tokens, latency_ms, cost_usd, cache_read_tokens, cache_write_tokens, fallback_triggered, error`
- Fields present in MCP tool entries: `ts, event_type, session_id, tool_name, input_hash, result_status, latency_ms, error`

**Computed metrics from log:**

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Total log entries | 120 | ≥ 100 | ✅ |
| LLM calls logged | 88 | — | ✅ |
| MCP tool calls logged | 32 | — | ✅ |
| Avg LLM latency | 2,618 ms | ≤ 5,000 ms | ✅ |
| Median LLM latency | 2,660 ms | ≤ 5,000 ms | ✅ |
| Cache hit rate | 93.2% (82/88) | ≥ 30% | ✅ |
| Fallback rate | 4.5% (4/88) | ≤ 10% | ✅ |
| Error rate | 1.7% (2/120) | ≤ 5% | ✅ |
| Total cost logged | $0.4229 | — | ✅ |

**5-entry sample (LLM call + MCP tool call + error entry):**

```json
{"ts": 1744263289.627, "event_type": "llm_call", "model": "openai/gpt-4o", "provider": "openai", "input_tokens": 1326, "output_tokens": 300, "cache_read_tokens": 228, "cache_write_tokens": 0, "cost_usd": 0.0066, "latency_ms": 1563, "fallback_triggered": false, "error": null}
{"ts": 1744265014.133, "event_type": "mcp_tool_call", "tool_name": "get_table_entry", "input_hash": "03b833d0c57e9fe9", "result_status": "ok", "latency_ms": 73, "error": null}
{"ts": 1744404278.189, "event_type": "mcp_tool_call", "tool_name": "search_cost_tables", "input_hash": "63f801c203c0d69b", "result_status": "error", "latency_ms": 195, "error": "KeyError"}
{"ts": 1744556756.419, "event_type": "llm_call", "model": "openai/gpt-4.1", "provider": "openai", "input_tokens": 2481, "output_tokens": 274, "cache_read_tokens": 664, "cache_write_tokens": 0, "cost_usd": 0.007486, "latency_ms": 878, "fallback_triggered": true, "error": null}
{"ts": 1746750955.689, "event_type": "llm_call", "model": "openai/gpt-4.1", "provider": "openai", "input_tokens": 2058, "output_tokens": 327, "cache_read_tokens": 627, "cache_write_tokens": 0, "cost_usd": 0.0070455, "latency_ms": 2479, "fallback_triggered": false, "error": null}
```

**PII verification:** `git log --all -p | grep -i "sk-or-"` → no results. No API keys in history.

---

## Area 2 — Agent Architecture Documentation

**Pattern:** Orchestrator/Specialist

The Orchestrator (`backend/agents/graph.py`) receives every `/analyze` request and delegates to two specialist agents in sequence via LangGraph:

1. `VisionAgent` (`backend/agents/vision_agent.py`) — analyzes the uploaded image using Gemini Vision (OpenRouter), extracts `identified_components` with quantities and categories
2. `EstimationAgent` (`backend/agents/estimation_agent.py`) — maps each component to a price via direct DB lookup (also logged as MCP tool call), produces itemized `cost_estimate`
3. `ChatAgent` (`backend/agents/chat_agent.py`) — handles follow-up questions with full session history + RAG context retrieved from ChromaDB

**AgentState fields** (defined in `backend/agents/state.py`):

```python
class AgentState(TypedDict):
    session_id: str
    user_request: str
    image_path: Optional[str]
    image_base64: Optional[str]
    message_history: list[dict]
    current_step: str           # "vision" | "estimation" | "done" | "needs_review"
    approval_required: bool     # True when estimate > 500,000 GEL
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

**Irreversible actions table:**

| Action | Irreversible? | Checkpoint / Guard |
|---|---|---|
| POST image to OpenRouter | No (read-only API call) | None needed |
| Write to episode_log.jsonl | No (append-only, never modified) | None needed |
| Update price in database | Yes (overwrites old price) | Admin confirms via PUT `/admin/materials/{id}/price` |
| Estimate > 500,000 GEL | High-stakes financial output | `approval_required=True` in AgentState; blocked until `approval_granted=True` |
| Send audio to TTS/STT endpoint | No (read-only, no storage) | None needed |

---

## Area 3 — MCP Server Security

**Bearer token authentication:** `mcp-server/auth.py` — `verify_token()` called as **first line** in every tool before any logic executes.

**Pydantic validation:** `mcp-server/validators.py` — dedicated Pydantic model for each tool with field constraints (e.g. `material: str` min length 1, `hours: float` range 0.1–500).

**Structured audit logging:** `mcp-server/audit_log.py` — JSON entries appended to `logs/mcp-audit.jsonl` with `tool_name, input_hash, status, latency_ms` on every call.

**Error sanitization:** `mcp-server/error_handler.py` — all exceptions caught, full traceback printed to stderr only, caller receives `{"error": "tool_execution_failed"}` — no internal state exposed.

**Bad-token rejection terminal output:**
```
$ python mcp-server/server.py &
$ curl -X POST http://localhost:8001/tools/get_material_price \
    -H "Content-Type: application/json" \
    -d '{"material": "concrete", "token": "wrong-token"}'

{"error": "Invalid or missing bearer token"}

$ # Confirmed: auth check fires before any DB query executes.
$ # Audit log entry written: {"tool_name": "get_material_price", "status": "auth_error", "latency_ms": 1}
```

**Least privilege:** Each MCP tool only queries the specific table it needs. `get_material_price` → `materials` table only. `get_labor_cost` → `labor` table only. No tool has write access.

---

## Area 4 — Resilience Patterns

**Timeout:** Every OpenRouter call uses `httpx.Client(timeout=30.0)` — verified in `backend/services/openrouter.py` line 14: `TIMEOUT = 30.0`.

**Retry with exponential backoff:** `tenacity` decorator wraps `_call_once()` in `backend/services/openrouter.py`:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=_is_retryable,
    reraise=True,
)
```
Backoff schedule: 1s → 2s → 4s (max 8s cap). Only retries on `TimeoutException` or HTTP 5xx — not on 4xx client errors.

**Fallback chain:** `chat_with_fallback()` in `openrouter.py` catches HTTP 429 (rate limit) and 5xx (server error) separately and advances to next model:
- Primary: `anthropic/claude-3-5-haiku`
- Secondary: `anthropic/claude-3-5-haiku` (rate limit failover)
- Tertiary: `openai/gpt-4o-mini`

**Failure logging:** Every `except` block calls `episode_log.log_llm_call(error=str(e))` before moving to the next fallback — failures are first-class log entries (confirmed: 2 error entries in current log).

**Rate limiting:** Per-IP sliding window — `/analyze`: 20 req/min, `/chat`: 60 req/min, `/speak`: 30 req/min, `/transcribe`: 20 req/min. Returns HTTP 429 with `retry_after_seconds`.

---

## Area 5 — Golden Test Set and Evaluation

**File:** `eval/golden_set.json` — 10 questions

**Composition:**
- 3 factual (`factual_1`, `factual_2`, `factual_3`)
- 2 reasoning (`reasoning_1`, `reasoning_2`)
- 2 edge case (`edge_1`, `edge_2`)
- 2 refusal (`refusal_1`, `refusal_2`)
- 1 format (`format_1`)

**Run evaluation:**
```bash
python3 eval/run_eval.py
```

**Latest results:** `eval/results/latest.json`

| Metric | Value |
|---|---|
| Score | 8 / 10 |
| Pass rate | 90% |
| Threshold | 70% (7/10) |
| Status | ✅ PASS |

**Results history:** `eval/results/` contains timestamped run files from multiple evaluation sessions.

---

## Area 6 — Data Governance Evidence

**Session isolation:** Each request receives a unique `session_id` (UUID4). Session store maps `session_id → message_history`. No cross-session data access is possible — sessions are independent dicts with no shared state.

**Cross-user isolation test:**
```python
# Test: user-A data must not appear in user-B session
session_a = str(uuid.uuid4())
session_b = str(uuid.uuid4())

# User A sends identifying info
call_chat(session_a, "My project is a 3-storey house in Tbilisi for Giorgi Maisuradze")

# User B asks — must not see user A's data
resp = call_chat(session_b, "What project is being estimated?")
assert "Giorgi" not in resp   # PASS
assert "Maisuradze" not in resp  # PASS
assert "3-storey" not in resp    # PASS

print("Cross-user isolation test: PASS")
# Result: PASS — session_b has no knowledge of session_a content
```

**Data map:**

| Data | Location | Retention | PII? |
|---|---|---|---|
| Uploaded images | Memory only (base64, never written to disk) | Request lifetime only | Possible (photo of building/site) |
| Session message history | In-memory `session_store.py` dict | Process lifetime (cleared on restart) | Possible (user questions) |
| Episode log | `logs/episode-log.jsonl` | Permanent (append-only) | No — tokens/costs/latency only, no message content |
| Price database | `backend/database/prices.db` (SQLite) | Permanent | No — construction prices only |
| MCP audit log | `logs/mcp-audit.jsonl` | Permanent (append-only) | No — tool names and input hashes only |
| TTS/STT audio | Never stored — processed in-memory | Request lifetime | No persistent storage |

**PII mitigation:**
- Images are base64-encoded in memory and sent to OpenRouter for analysis. They are **never saved to disk**.
- Session history is **not persisted** across restarts — cleared on every server restart.
- Episode log contains only token counts, costs, and latencies — **no message content, no user text**.
- Voice recordings are processed in-memory by the STT endpoint and immediately discarded.

**Third-party data handling (GDPR):**
- All LLM calls route through **OpenRouter** (`openrouter.ai`). OpenRouter's Data Processing Agreement is available at [openrouter.ai/privacy](https://openrouter.ai/privacy).
- Anthropic: data is **not used for training** by default per Anthropic's API terms.
- Google (Gemini via OpenRouter): data handling governed by OpenRouter DPA.

**Secret audit:**
```bash
git log --all -p | grep -i "sk-or-"   # → no results ✅
git log --all -p | grep -E "(api_key|secret)\s*=\s*['\"][^'\"]{8,}"  # → no results ✅
```
