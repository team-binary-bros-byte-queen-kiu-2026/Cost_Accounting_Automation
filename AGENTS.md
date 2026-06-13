# AGENTS.md — ConstructAI

Guide for AI coding agents (Claude Code, Cursor, Copilot, etc.) working in this repository.

## What this repo is

ConstructAI is an AI-powered construction cost estimator for the Georgian market. Users upload a photo of a building → the system returns an itemized GEL cost estimate → users can ask follow-up questions via streaming chat.

**Live app:** https://cost-accounting-automation.vercel.app

## Repo layout

```
backend/          FastAPI app — agents, routers, services, database
frontend/         Next.js 14 app
mcp-server/       MCP tool server (bearer token auth, port 8001)
eval/             Golden set + model comparison scripts
load/             Locust load test
logs/             Episode log (append-only JSONL)
rag-data/         Markdown knowledge base + ingest script
docs/             All documentation
```

## Key entry points

| File | Purpose |
|---|---|
| `backend/main.py` | FastAPI app factory — registers all routers |
| `backend/agents/graph.py` | LangGraph pipeline: VisionAgent → EstimationAgent → (approval gate) |
| `backend/agents/chat_agent.py` | ChatAgent with session memory + RAG |
| `backend/services/openrouter.py` | All LLM calls, fallback chain, prompt caching |
| `backend/services/session_store.py` | In-memory session store (estimate + history) |
| `mcp-server/server.py` | MCP tool server entry point |

## Rules for agents

### Never touch
- `logs/episode-log.jsonl` — append-only, do not rewrite or truncate
- `.env` — never read or write real secrets
- `eval/results/` — do not delete existing run files

### Model names
All model names come from environment variables (`PRIMARY_MODEL`, `SECONDARY_MODEL`, `OSS_FALLBACK`, `PRIMARY_VISION_MODEL`). Never hardcode a model string in source code.

### Fallback chain
The fallback order is always Primary → Secondary → OSS Fallback. Do not change this order without updating `docs/model-selection.md`.

### Episode logging
Every LLM call and MCP tool call must produce an entry in `logs/episode-log.jsonl`. The schema is in `backend/services/episode_log.py`. Do not add PII (message content, user text) to log entries.

### Database
`backend/database/seed_prices.py` seeds the SQLite price database. Run it after any schema change. The DB file is gitignored.

### Tests
```bash
python eval/run_eval.py          # golden set — must score ≥ 70%
python eval/run_model_comparison.py  # model benchmark
```

### Adding a new route
1. Create `backend/routers/yourroute.py`
2. Register in `backend/main.py` with `app.include_router(...)`
3. Add rate limit in `backend/services/rate_limiter.py`
4. Document the endpoint in `README.md`

### MCP tools
All MCP tools must call `verify_token()` as the first line. All inputs must be validated with a Pydantic model in `mcp-server/validators.py`. Errors must be caught and returned as `{"error": "tool_execution_failed"}` — no tracebacks to callers.
