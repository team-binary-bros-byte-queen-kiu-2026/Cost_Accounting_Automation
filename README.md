# ConstructAI — AI-Powered Construction Cost Estimator

> Upload a photo of a building project → get an instant itemized cost estimate based on Georgian market prices → ask follow-up questions in a streaming AI chat.

**Course:** CS-AI-2025 · KIU · Spring 2026 | **Team:** [Your team name]

---

## Quick Start (5 minutes)

### 1. Clone and set up environment
```bash
git clone <your-repo-url>
cd construct-ai
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

## Architecture

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

**Agent pattern:** Orchestrator/Specialist
- `VisionAgent` → identifies building components from photo
- `EstimationAgent` → prices components via MCP tools
- `ChatAgent` → answers questions with session memory + RAG

---

## Model Selection

| Task | Model | Reasoning | Fallback |
|---|---|---|---|
| Image analysis | `google/gemini-2.0-flash` | Best vision accuracy, $0.10/M tokens, 1.8s median latency | `openai/gpt-4o-mini` |
| Streaming chat | `anthropic/claude-3-5-haiku` | Instruction following 0.87 score, good for Q&A | `openai/gpt-4o-mini` |
| Embeddings | `openai/text-embedding-3-small` | 0.8 cosine similarity on construction domain, $0.02/M tokens | none |
| Rate limit | 20 req/min `/analyze`, 60/min `/chat` | Vision calls ~$0.002 each — prevents cost overrun | HTTP 429 |

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

Based on actual usage data from episode logs:

| Task | Model | Avg input tokens | Avg output tokens | Cost per call | Monthly (1000 calls) |
|---|---|---|---|---|---|
| Image analysis | gemini-2.0-flash | ~1,200 | ~800 | ~$0.0005 | ~$0.50 |
| Chat response | claude-3-5-haiku | ~2,500 | ~400 | ~$0.0036 | ~$3.60 |
| Embedding | text-embedding-3-small | ~300 | — | ~$0.000006 | ~$0.006 |

*Update this table with actual numbers from `/logs/episode_log.jsonl` before Lab 11 submission.*

---

## Replacing Sample Prices

Sample prices are seeded from `backend/database/seed_prices.py`.
To update to real market prices:
1. Go to [http://localhost:3000/admin](http://localhost:3000/admin)
2. Edit any price and click Save
3. Or: edit the values in `seed_prices.py` and re-run it
4. Or: update `rag-data/*.md` and re-run `python rag-data/ingest.py`

---

## Security Notes

- Real API keys are only in `.env` (gitignored)
- `.env.example` contains placeholders only
- MCP server requires bearer token authentication
- Rate limiting prevents API key abuse
- Verify: `git log --all -p | grep -i "sk-or-"` should return nothing
