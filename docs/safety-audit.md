# Safety and Evaluation Audit

**Team Name:** Binary Bros & Byte Queen
**Team Members:** Guga Gagloshvili, Ilia Pkhakadze, Nikoloz Rusishvili, Anastasia
**Repository:** https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation
**Audit Commit:** lab8-mcp-capstone (see tag; latest commit SHA updated after tagging)
**Submitted:** 14 May 2026

## Area 1: Episode Log Quality — /2 pts

**Link to episode log file:**
https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation/blob/main/logs/episode-log.jsonl

**Total entry count:**
120 entries (88 LLM call entries + 32 MCP tool call entries)

Verified with: `wc -l logs/episode-log.jsonl` → `120`

**Sample — 5 consecutive entries:**

```json
{"ts": 1744263289.627, "event_type": "llm_call", "model": "openai/gpt-4o", "provider": "openai", "input_tokens": 1326, "output_tokens": 300, "cache_read_tokens": 228, "cache_write_tokens": 0, "cost_usd": 0.0066, "latency_ms": 1563, "fallback_triggered": false, "error": null}
{"ts": 1744265014.133, "event_type": "mcp_tool_call", "tool_name": "get_table_entry", "input_hash": "03b833d0c57e9fe9", "result_status": "ok", "latency_ms": 73, "error": null}
{"ts": 1744300753.182, "event_type": "llm_call", "model": "openai/gpt-4o", "provider": "openai", "input_tokens": 2432, "output_tokens": 479, "cache_read_tokens": 451, "cache_write_tokens": 0, "cost_usd": 0.01143375, "latency_ms": 4099, "fallback_triggered": false, "error": null}
{"ts": 1744302310.089, "event_type": "llm_call", "model": "openai/gpt-4o", "provider": "openai", "input_tokens": 1928, "output_tokens": 82, "cache_read_tokens": 30, "cache_write_tokens": 0, "cost_usd": 0.0056775, "latency_ms": 1187, "fallback_triggered": false, "error": null}
{"ts": 1744328294.524, "event_type": "mcp_tool_call", "tool_name": "search_cost_tables", "input_hash": "a1c4f8b2d3e90001", "result_status": "ok", "latency_ms": 148, "error": null}
```

**Confirm all required fields are present on LLM call entries:**

- [x] ts
- [x] event_type: "llm_call"
- [x] model
- [x] provider
- [x] input_tokens
- [x] output_tokens
- [x] cache_read_tokens (may be 0, present on every entry)
- [x] cache_write_tokens (may be 0, present on every entry)
- [x] cost_usd
- [x] latency_ms
- [x] fallback_triggered
- [x] error (may be null, present on every entry)

**Confirm MCP tool call entries exist:**

- [x] ts
- [x] event_type: "mcp_tool_call"
- [x] tool_name
- [x] input_hash
- [x] result_status
- [x] latency_ms

---

## Area 2: Agent Architecture Documentation — /1 pt

**Link to Agent Architecture section in README:**
https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation/blob/main/README.md#agent-architecture

**Pattern in use:** Pipeline

**One-sentence justification:**
We chose the pipeline pattern because every user request follows a fixed three-stage
sequence (preprocessing → RAG retrieval → LLM generation) with no dynamic tool selection,
making a pipeline simpler and more predictable than an orchestrator/specialist arrangement.

**Confirm all four elements are present in the README section:**

- [x] Pattern choice stated with justification
- [x] AgentState dataclass with all fields named and typed
- [x] List of every irreversible action the agent can take
- [x] Each irreversible action mapped to its checkpoint or guard

---

## Area 3: MCP Server Security — /2 pts

**Link to MCP server source code:**
https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation/blob/main/mcp-server/server.py

### Auth Test Output

Called `search_cost_tables` with `_auth_token: "wrong_token"`:

```
$ MCP_SECRET_KEY=correct_secret python3 -c "
import asyncio, json
from mcp_server.server import call_tool
result = asyncio.run(call_tool('search_cost_tables', {'_auth_token': 'wrong_token', 'query': 'test'}))
print(result[0].text)
"
{"error": "unauthorized"}
```

Confirm the output is a structured JSON error (not a traceback): [x]

### Input Validation Code Snippet

Pydantic schema for `search_cost_tables` (from `mcp-server/server.py`):

```python
class SearchCostTablesInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=600,
                       description="Natural language search query about construction costs")
    max_results: int = Field(default=5, ge=1, le=20,
                             description="Number of results to return (1-20)")
    table_category: str = Field(default="all",
                                description="Filter by category: materials | labour | overhead | all")
```

Called with missing `query` field → returns `{"error": "invalid_input"}` before any tool logic runs.

### MCP Audit Log Sample

From `logs/mcp-audit.jsonl` (3 entries):

```json
{"ts": 1747008001.123, "event_type": "mcp_tool_call", "tool_name": "search_cost_tables", "input_hash": "d4e7f1a2b3c89012", "result_status": "ok", "latency_ms": 187, "error": null}
{"ts": 1747008042.441, "event_type": "mcp_tool_call", "tool_name": "search_cost_tables", "input_hash": "00000000", "result_status": "auth_failed", "latency_ms": 2, "error": null}
{"ts": 1747008089.882, "event_type": "mcp_tool_call", "tool_name": "get_table_entry", "input_hash": "e5f8a3b4c1d20934", "result_status": "error", "latency_ms": 312, "error": "KeyError"}
```

### Error Sanitisation Test

**What we broke:** Commented out the `do_search` function body to raise `AttributeError`.

**What the caller received:**
```json
{"error": "tool_execution_failed"}
```

No traceback, file path, or environment variable name was exposed to the caller.
The full traceback was captured by `server_logger.error(..., exc_info=True)` server-side only.

Confirm it contains no traceback, file paths, or environment variable names: [x]

---

## Area 4: Resilience Patterns — /1 pt

### Timeout Implementation

From `backend/llm_client.py`:

```python
LLM_TIMEOUT_SECONDS = 30

data = await asyncio.wait_for(
    _call_once(current_model, messages, temperature, max_tokens, timeout),
    timeout=timeout,
)
```

`asyncio.wait_for` wraps every single LLM call. Timeout is configurable via the
`timeout` parameter; default is 30 seconds.

Confirm timeout is applied to every LLM call (not just one): [x]
All calls go through the `call_llm()` function which always applies this wrapper.

### Retry and Backoff Implementation

From `backend/llm_client.py`:

```python
MAX_RETRIES = 3
BACKOFF_BASE = 1.0  # seconds; doubled each retry

for attempt in range(MAX_RETRIES):
    try:
        data = await asyncio.wait_for(...)
        # success — return result
    except (asyncio.TimeoutError, httpx.HTTPStatusError, httpx.RequestError) as e:
        last_error = type(e).__name__
        if attempt == MAX_RETRIES - 2 and current_model == model and fallback_model:
            model = fallback_model          # switch to fallback on penultimate retry
            fallback_triggered = True
        if attempt < MAX_RETRIES - 1:
            backoff = BACKOFF_BASE * (2 ** attempt)   # 1s → 2s → 4s
            await asyncio.sleep(backoff)
        else:
            raise RuntimeError(f"All {MAX_RETRIES} attempts failed.")
```

Confirm retry uses exponential backoff with at least 2 retries: [x]
3 attempts total, backoff sequence: 1 s, 2 s.

---

## Area 5: Golden Test Set and Evaluation — /2 pts

**Link to golden set file:**
https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation/blob/main/eval/golden_set.json

**Link to evaluation script:**
https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation/blob/main/eval/run_golden_set.py

**Link to most recent results file:**
https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation/blob/main/eval/results/

### Results Summary

*(Run `python3 eval/run_golden_set.py` live in Week 11 lab to produce this table)*

| Question ID | Category | Pass/Fail | Reason (if fail) |
|---|---|---|---|
| g001 | factual | | |
| g002 | factual | | |
| g003 | reasoning | | |
| g004 | reasoning | | |
| g005 | refusal | | |
| g006 | refusal | | |
| g007 | edge_case | | |
| g008 | edge_case | | |
| g009 | format | | |
| g010 | format | | |

**Overall score:** [X]/10 ← to be filled after live run in Week 11 lab

---

## Area 6: Data Governance Evidence — /2 pts

### Cross-User Isolation Test

**Test procedure:**
1. Create User A and User B accounts.
2. User A uploads a project document and creates project `project-alpha`.
3. Log in as User B.
4. Issue a GET request to `/api/projects/project-alpha` using User B's JWT token.
5. Confirm the response is `{"error": "not_found"}` (not `403 forbidden`, to avoid confirming the project exists).

**Test output:**
```
$ curl -H "Authorization: Bearer $USER_B_TOKEN" http://localhost:8000/api/projects/project-alpha
{"error": "not_found"}

User B cannot read User A's project data. Isolation confirmed.
```

All MongoDB queries are scoped by `user_id` field extracted from the verified JWT token.
No project query runs without a `{user_id: $current_user}` filter.

### Data Retention Policy

**Link to data-map.md:**
https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation/blob/main/docs/data-map.md

**Summary of what is stored and for how long:**

| Data Type | Storage Location | Retention Period | Deletion Method |
|---|---|---|---|
| User account data | MongoDB Atlas (EU) | Until account deletion | "Delete account" in settings |
| Uploaded project documents | AWS S3 (EU Frankfurt) | Project lifetime + 30 days | "Delete project" action or account deletion |
| Extracted structured data | MongoDB Atlas (EU) | Project lifetime + 30 days | Same as above |
| Chat query history | MongoDB Atlas (EU) | Session only | Session end |
| Episode log | Local → S3 after 30 days | 90 days rolling | Automated cleanup |

### PII in Episode Log

**Command run:**
```bash
grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" logs/episode-log.jsonl
```

**Output:** *(empty — no matches)*

The episode log contains only operational metrics (timestamps, model names, token counts,
costs, latencies, error codes). No user query text, email addresses, or personal data.

### API Key Security

**Command run:**
```bash
git log --all --full-history -- .env
```

**Output:** *(empty — .env was never committed)*

`.env` has been listed in `.gitignore` since the first commit. Confirmed clean.

---

## Model Selection Decisions Table

*(Reproduced from README for completeness)*

| Call Location | Current Model | Reason | Alternative Considered |
|---|---|---|---|
| Document parsing (PDF → JSON) | `openai/gpt-4o` | Strong structured extraction from mixed-format PDFs | `claude-sonnet-4-5`: comparable but 2× cost |
| Chatbot Q&A (RAG) | `openai/gpt-4.1` | High reasoning for professional domain Q&A; citation compliance | `openai/gpt-4o`: slightly less reasoning depth |
| Chatbot fallback | `openai/gpt-4o-mini` | Lowest cost; adequate for simple lookups | `google/gemini-2.0-flash`: consistent but less reliable JSON |
| Embeddings | `openai/text-embedding-3-large` | Highest recall on technical Georgian text | `text-embedding-3-small`: 5× cheaper, 8% lower recall |
| Voice transcription | `openai/whisper-1` | Best accuracy on Georgian-accented speech | No viable alternative tested |
| LLM-as-judge (eval) | `google/gemini-2.5-flash-preview` | Fast, cheap, consistent JSON for binary eval | `gpt-4o-mini`: similar cost, less consistent output |

---

## Live Verification Preparation

Confirm ready for Week 11 lab (Friday 15 May):

- [ ] `python3 eval/run_golden_set.py` runs to completion without errors
- [x] MCP auth rejection demo: `_auth_token: "wrong"` → `{"error": "unauthorized"}` — reproducible
- [x] Cross-user isolation: MongoDB query always scoped by `user_id` from JWT — documented above
- [ ] Team members know who demos each check: Nikoloz → golden set run; Guga, Anastasia and Ilia → MCP auth, data governence and isolation test

---
