# ConstructAI — AI-Powered Construction Cost Estimator

> Upload a photo of a building project → get an instant itemized cost estimate based on Georgian market prices → ask follow-up questions in a streaming AI chat.

**Course:** CS-AI-2025 · KIU · Spring 2026 | **Team:** Binary Bros & Byte Queens

---

## Quick Start (5 minutes)

### 1. Clone and set up environment
```bash
git clone https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation.git
cd Cost_Accounting_Automation
cp .env.example .env
# Edit .env: add OPENROUTER_API_KEY and MCP_BEARER_TOKEN
```

### 2. Start the backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python database/seed_prices.py    # seed SQLite with sample prices
uvicorn main:app --reload --port 8000
```

### 3. (Optional) Ingest RAG knowledge base
```bash
cd ..
python rag-data/ingest.py
```

### 4. Start the frontend
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 5. (Optional) Start the MCP server
```bash
cd mcp-server
pip install -r requirements.txt
python server.py
# Inspect: npx @modelcontextprotocol/inspector python server.py
```

---

## Agent Architecture

**Pattern:** Orchestrator/Specialist (LangGraph)

The `/analyze` pipeline is orchestrated by `backend/agents/graph.py`. A single request flows through specialist agents in sequence; follow-up chat uses a separate `ChatAgent` with session memory.

| Agent | Role | Input | Output |
|---|---|---|---|
| `VisionAgent` | Identifies building components from photo | `image_base64` | `identified_components` |
| `EstimationAgent` | Prices each component via DB / MCP tools | `identified_components` | `cost_estimate` |
| `ChatAgent` | Answers follow-up questions with RAG + history | user message + session | streamed text |

### AgentState

Defined in `backend/agents/state.py`:

```python
class AgentState(TypedDict):
    session_id: str
    user_request: str
    image_path: Optional[str]
    image_base64: Optional[str]
    message_history: list[dict]
    current_step: str                  # vision | estimation | done | needs_review
    approval_required: bool            # True when estimate > 500,000 GEL
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

### Irreversible actions

| Action | Irreversible? | Checkpoint / guard |
|---|---|---|
| POST image to OpenRouter | No (read-only API call) | None |
| Append to episode log | No (append-only) | None |
| Update material price in DB | Yes (overwrites old price) | Admin confirms via `PUT /admin/materials/{id}/price` |
| Estimate > 500,000 GEL | High-stakes output | `approval_required=True` until `approval_granted=True` |
| TTS / STT audio processing | No (in-memory only) | Audio never persisted to disk |

### System diagram

```
[User browser]
    │  Upload image / send message
    ▼
[Next.js 14 frontend]  ←→  [FastAPI backend :8000]
                                │
                    ┌───────────┼───────────────────┐
                    ▼           ▼                   ▼
             [OpenRouter]  [SQLite DB]        [ChromaDB]
           (Gemini Vision,  (prices,          (RAG vector
            Claude Haiku,   sessions)          store)
            GPT-4o-mini)
                    │
                    ▼
             [MCP Server :8001]
             (price tools + RAG tools)
```

### LLM fallback chain

Configured in `backend/settings.py` (env vars: `PRIMARY_MODEL`, `SECONDARY_MODEL`, `OSS_FALLBACK`):

```
Vision:  PRIMARY_VISION_MODEL → SECONDARY_MODEL → OSS_FALLBACK
Chat:    PRIMARY_MODEL         → SECONDARY_MODEL → OSS_FALLBACK
              │                        │                  │
              ▼                        ▼                  ▼
     google/gemini-2.5-flash    claude-3-5-haiku    gpt-4o-mini
```

On 429 or 5xx, `chat_with_fallback()` and `stream_chat()` advance to the next model and log `fallback_triggered=true` in the episode log.

---

## Model Selection Decisions

| Task | Model | Why | Fallback |
|---|---|---|---|
| Image analysis (`/analyze`) | `google/gemini-2.5-flash` | Strong multimodal accuracy, $0.075/M input, best benchmark quality/cost | `anthropic/claude-3-5-haiku` → `openai/gpt-4o-mini` |
| Streaming chat (`/chat/stream`) | `anthropic/claude-3-5-haiku` | Reliable instruction following for short GEL cost answers | `anthropic/claude-3-5-haiku` (429 failover) → `openai/gpt-4o-mini` |
| RAG embeddings | `openai/text-embedding-3-small` | Good cosine similarity on construction domain text, $0.02/M tokens | none (local ChromaDB retrieval) |
| Text-to-speech (`/speak`) | `openai/tts-1` | Low-latency speech via OpenRouter | HTTP 502 to client |
| Speech-to-text (`/transcribe`) | `openai/whisper-1` | Accurate Georgian/English transcription | HTTP 502 to client |

Models are loaded from environment variables — see `.env.example`. Never hardcoded in call sites.

### Why we did not use o3

OpenAI o3 latency (8–15 s per call) is incompatible with real-time streaming chat. ConstructAI targets sub-3 s full responses; Haiku and Gemini Flash meet that budget.

### Fallback strategy

```
Primary model
    → Secondary model (same provider or alternate)
        → OSS fallback (gpt-4o-mini via OpenRouter)
            → Error response to client (no raw traceback)
```

Every LLM call sets `"data_collection": "deny"` on OpenRouter requests (GDPR). See `docs/safety-audit.md` for full data governance evidence.

### Cost analysis

From `logs/episode-log.jsonl` + `logs/episode_log.jsonl` (153 entries, regenerate via `python backend/scripts/metrics_report.py`):

| Task | Model | Avg input tokens | Avg output tokens | Cost per call | Monthly (1000 calls) |
|---|---|---|---|---|---|
| Image analysis | gemini-2.5-flash | ~1,200 | ~800 | ~$0.00036 | ~$0.36 |
| Chat response | claude-3-5-haiku | ~2,500 | ~400 | ~$0.0036 | ~$3.60 |
| Embedding | text-embedding-3-small | ~300 | — | ~$0.000006 | ~$0.006 |

**Total logged LLM spend:** ~$0.44 · **Cache hit rate:** 67.8% · **Eval pass rate:** 7/10 (70%)

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check — `{"status":"ok"}` in <500ms |
| POST | `/analyze` | Upload image → cost estimate |
| POST | `/chat/stream` | SSE streaming chat |
| POST | `/speak` | Text → MP3 audio (TTS) |
| POST | `/transcribe` | Audio → text (STT) |
| GET | `/admin/materials` | List all material prices |
| PUT | `/admin/materials/{id}/price` | Update a material price |

---

## Running Tests

```bash
# Start backend first, then:
python eval/run_eval.py
python eval/run_model_comparison.py   # Lab 11 benchmark → eval/model-comparison.json
# Must score ≥ 70% to pass CI
```

---

## Docker

```bash
cd backend
docker build -t construct-ai-backend .
docker run -p 8000:8000 --env-file ../.env construct-ai-backend
curl http://localhost:8000/health
```

---

## Lab Checkpoints

| Tag | Lab | What was delivered |
|---|---|---|
| `lab5-checkpoint` | Lab 5 | First working `/analyze` endpoint + cost log |
| `lab6-mcp-checkpoint` | Lab 6 | SSE streaming chat + session memory + MCP server |
| `lab7-agent-architecture-checkpoint` | Lab 7 | LangGraph orchestration + AgentState + resilience |
| `lab8-mcp-capstone` | Lab 8 | MCP production security + prompt caching + optimization report |
| `lab9-hardening` | Lab 9 | Golden set eval + metrics report + model selection review |
| `lab10-production` | Lab 10 | Secrets audit + CI/CD + Docker + rate limiting |
| `lab11-portability` | Lab 11 | Model benchmark + fallback chain + cost analysis |

---

## Cost Analysis

See **Cost analysis** under [Model Selection Decisions](#model-selection-decisions) above. Full computed metrics: [`docs/metrics-report.md`](docs/metrics-report.md).

---

## Replacing Sample Prices

Sample prices are seeded from `backend/database/seed_prices.py`.
To update to real market prices:
1. Go to [http://localhost:3000/admin](http://localhost:3000/admin)
2. Edit any price and click Save
3. Or: edit the values in `seed_prices.py` and re-run it
4. Or: update `rag-data/*.md` and re-run `python rag-data/ingest.py`

---

## Demo Video
https://youtu.be/64gd22-Ofqw



---

## Security Notes

- Real API keys are only in `.env` (gitignored)
- `.env.example` contains placeholders only
- MCP server requires bearer token authentication
- Rate limiting prevents API key abuse (20/min `/analyze`, 60/min `/chat`)
- Safety & eval audit: [`docs/safety-audit.md`](docs/safety-audit.md)
- Verify: `git log --all -p | grep -i "sk-or-"` should return nothing
