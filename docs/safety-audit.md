# Safety and Evaluation Audit
**Course:** CS-AI-2025 · Spring 2026
**Due:** Thursday May 21, 2026 at 23:59
**File:** docs/safety-audit.md

---

## Area 1 — Episode Log Quality

**Status:** ☐ To be completed by May 21

- Episode log location: `logs/episode_log.jsonl`
- Log format: JSONL (one JSON object per line)
- Fields present in LLM call entries: `ts, type, session_id, model, model_used, input_tokens, output_tokens, latency_ms, cost_usd, cache_read_tokens, cache_write_tokens, fallback_triggered, error`
- Fields present in MCP tool entries: `ts, type, session_id, tool_name, input_hash, status, latency_ms, error`

*[Replace with actual entry count and sample entries before submission]*

---

## Area 2 — Agent Architecture Documentation

**Pattern:** Orchestrator/Specialist

The Orchestrator receives every analysis request and delegates to:
1. `VisionAgent` — analyzes the uploaded image using Gemini Vision, outputs `identified_components`
2. `EstimationAgent` — maps components to prices via MCP tools, outputs `cost_estimate`
3. `ChatAgent` — handles follow-up questions with full session history + RAG context

**AgentState fields** (defined in `backend/agents/state.py`):
`session_id, user_request, image_path, image_base64, message_history, current_step, approval_required, approval_granted, retry_count, timeout_ms, identified_components, cost_estimate, model_used, fallback_triggered, cache_read_tokens, cache_write_tokens, latency_ms, error`

**Irreversible actions table:**

| Action | Irreversible? | Checkpoint |
|---|---|---|
| POST image to OpenRouter | No (read-only API call) | None needed |
| Write to episode_log.jsonl | No (append-only) | None needed |
| Update price in database | Yes (overwrites old price) | Admin confirms via PUT endpoint |
| Estimate >500,000 GEL | Flagged as high-stakes | `approval_required=True` in AgentState |

---

## Area 3 — MCP Server Security

**Bearer token authentication:** `mcp-server/auth.py` — `verify_token()` called as first line in every tool before any logic.

**Pydantic validation:** `mcp-server/validators.py` — dedicated Pydantic model for each tool with field constraints.

**Structured audit logging:** `mcp-server/audit_log.py` — JSON entries with `tool_name, input_hash, status, latency_ms`.

**Error sanitization:** `mcp-server/error_handler.py` — all exceptions caught, traceback printed to stderr only, caller receives `{"error": "tool_execution_failed"}`.

---

## Area 4 — Resilience Patterns

**Timeout:** Every OpenRouter call uses `httpx.Client(timeout=30.0)` — 30-second hard limit.

**Retry:** `tenacity` `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))` wraps every `_call_once()` in `backend/services/openrouter.py`.

**Failure logging:** The `except` blocks in `openrouter.py` call `episode_log.log_llm_call(error=str(e))` before continuing to next fallback model — failures are first-class log entries.

---

## Area 5 — Golden Test Set and Evaluation

**File:** `eval/golden_set.json` — 10 questions (3 factual, 2 reasoning, 2 edge case, 2 refusal, 1 format)

**Run evaluation:**
```bash
python eval/run_eval.py
```

**Pass threshold:** 70% (7/10 questions)

*[Replace with actual pass rate and results link before submission]*

---

## Area 6 — Data Governance Evidence

**Session isolation:** Each request receives a unique `session_id` (UUID). Session store maps `session_id → history`. No cross-session data access.

**Data map:**

| Data | Location | Retention | PII? |
|---|---|---|---|
| Uploaded images | Memory only (not written to disk) | Request lifetime | Possible (photo of house) |
| Session history | In-memory `session_store.py` | Process lifetime (cleared on restart) | Possible (user questions) |
| Episode log | `logs/episode_log.jsonl` | Permanent (append-only) | No (tokens/costs only) |
| Price database | `backend/database/prices.db` | Permanent | No |

**PII mitigation:** Images are base64-encoded in memory and sent to OpenRouter for analysis. They are not saved to disk. Session history is not persisted across restarts.

**Secret verification:** Run `git log --all -p | grep -i "sk-or-"` → should return nothing.
