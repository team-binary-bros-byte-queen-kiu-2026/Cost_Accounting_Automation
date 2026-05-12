# Cost Accounting Automation

**Course:** CS-AI-2025 — Building AI-Powered Applications | Spring 2026
**Team:** Binary Bros & Byte Queen
**Repo:** https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation

An AI-powered platform that automates the Georgian construction cost accounting workflow.
It converts thousands of legacy Soviet-era reference tables into a structured database,
enables automated compliant report generation from uploaded project documents,
and provides a RAG-powered chatbot for professional cost accounting Q&A.

---

## Agent Architecture

### Pattern: Pipeline (Sequential Stages)

We use a **pipeline** pattern with three sequential stages. This was chosen over
orchestrator/specialist because every user request follows the same deterministic flow:
retrieve → augment → generate. There is no dynamic tool selection or routing required
at the agent level.

```
User Query
    │
    ▼
┌─────────────────────────┐
│  Stage 1: Preprocessing │  — voice transcription (Whisper), input sanitisation
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Stage 2: RAG Retrieval │  — embed query, Pinecone top-k search, fetch MongoDB chunks
└────────────┬────────────┘
             │
             ▼
┌──────────────────────────┐
│  Stage 3: LLM Generation │  — GPT-4.1 + grounded context → cited answer
└──────────────────────────┘
             │
             ▼
        User Response
```

### AgentState

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class AgentState:
    # Input
    raw_query: str                          # original user input (text or transcribed audio)
    project_id: str                         # which project context to use
    user_id: str                            # for cross-user isolation enforcement

    # Stage 2 outputs
    query_embedding: list[float] = field(default_factory=list)   # text-embedding-3-large vector
    retrieved_chunks: list[dict] = field(default_factory=list)   # top-k Pinecone results
    retrieval_score: float = 0.0            # highest similarity score from retrieval

    # Stage 3 outputs
    llm_response: str = ""                  # raw model output
    citations: list[str] = field(default_factory=list)  # extracted table/regulation codes
    confidence: str = "high"               # "high" | "low" — drives fallback UX

    # Metadata
    fallback_triggered: bool = False
    error: Optional[str] = None
    latency_ms: int = 0
```

### Irreversible Actions and Guards

| Irreversible Action | Guard / Checkpoint |
|---|---|
| Writing extracted document data to MongoDB | Schema validation (Pydantic) must pass before write; write is idempotent by document hash |
| Generating and downloading a construction accounting report (PDF/Excel) | User must confirm a "Generate report" dialog before the backend assembles the file; no auto-generation |
| Deleting a project and all its uploaded documents | Requires explicit "Delete project" confirmation + re-type of project name; soft-delete for 30 days before hard delete |
| Sending uploaded document content to OpenAI API | Data processing agreement acceptance is enforced at the backend route level before any file is forwarded to the AI API |

---

## Model Selection Decisions

| Call Location | Current Model | Reason for Choice | Alternative Considered |
|---|---|---|---|
| Document parsing (PDF → JSON) | `openai/gpt-4o` | Strong structured extraction from mixed-format PDFs; handles scanned + digital | `claude-sonnet-4-5`: comparable quality but 2× cost |
| Chatbot Q&A (RAG) | `openai/gpt-4.1` | High reasoning accuracy for professional domain Q&A; citation compliance | `openai/gpt-4o`: slightly less reasoning depth at similar cost |
| Chatbot fallback | `openai/gpt-4o-mini` | Lowest cost; adequate for simple lookups when primary is unavailable | `google/gemini-2.0-flash`: comparable speed but less consistent citation format |
| Embeddings (vector search) | `openai/text-embedding-3-large` | Highest retrieval accuracy on technical/legal Georgian text | `text-embedding-3-small`: 5× cheaper but 8% lower recall on our test set |
| Voice transcription | `openai/whisper-1` | Best accuracy on Georgian-accented professional speech | No viable alternative tested |
| LLM-as-judge (eval) | `google/gemini-2.5-flash-preview` | Fast and cheap for binary pass/fail evaluation; free tier available | `gpt-4o-mini`: similar cost but less consistent JSON output format |

---

## Repository Structure

```
Cost_Accounting_Automation/
├── README.md
├── TEAM-CONTRACT.md
├── .gitignore
├── .env.example
│
├── backend/
│   ├── llm_client.py          ← LLM wrapper: timeout, retry, episode logging
│   └── README.md
│
├── frontend/
│   └── README.md
│
├── mcp-server/
│   └── server.py              ← Production MCP server (auth + validation + logging)
│
├── eval/
│   ├── golden_set.json        ← 10 cost-accounting evaluation questions
│   ├── run_golden_set.py      ← LLM-as-judge evaluation script
│   └── results/               ← Committed evaluation run outputs
│
├── scripts/
│   └── seed_episode_log.py    ← Dev utility to seed log entries
│
├── logs/
│   ├── episode-log.jsonl      ← LLM call metrics (120+ entries from Lab 6 onward)
│   └── mcp-audit.jsonl        ← MCP tool call audit entries
│
├── docs/
│   ├── design-review/
│   │   └── DESIGN-REVIEW.md
│   ├── data-map.md            ← Data governance document
│   ├── optimization-report.md ← Prompt caching benchmark
│   └── safety-audit.md        ← Safety and Evaluation Audit submission
│
├── lab-3/
│   └── generation-strategy.md
│
└── tests/
```

---

## Getting Started

```bash
# 1. Clone and set up
git clone https://github.com/team-binary-bros-byte-queen-kiu-2026/Cost_Accounting_Automation.git
cd Cost_Accounting_Automation
cp .env.example .env   # add your real keys

# 2. Install Python dependencies
pip install mcp pydantic python-dotenv httpx

# 3. Run the MCP server
MCP_SECRET_KEY=your_secret python3 mcp-server/server.py

# 4. Run the evaluation suite
export OPENROUTER_API_KEY=your_key
python3 eval/run_golden_set.py
```
