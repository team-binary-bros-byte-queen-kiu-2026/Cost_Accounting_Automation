# Data Map — ConstructAI

**Version:** 2.0  
**Last updated:** 8 June 2026  
**Owner:** Binary Bros & Byte Queens

This document describes every category of data the application collects or processes,
where it is stored, how long it is retained, and how it can be deleted.
It satisfies the data governance requirement from the Design Review and the Safety Audit.

**Scope:** This map reflects the **implemented** capstone stack (FastAPI + SQLite + in-memory
sessions + local ChromaDB + JSONL logs). There is no user authentication, MongoDB, S3, or
Pinecone in the current codebase.

---

## 1. SQLite Database

**File:** `backend/database/prices.db` (path configurable via `DATABASE_PATH` in `.env`)  
**Engine:** SQLite 3, single-file, local filesystem  
**Encryption at rest:** No (development / local deployment)

### 1.1 Table: `materials`

| Column | Type | Contents | Sensitivity |
|---|---|---|---|
| `id` | INTEGER PK | Auto-increment row ID | Low |
| `name` | TEXT | Material name (e.g. concrete, rebar) | Public |
| `category` | TEXT | Category slug (concrete, masonry, steel, …) | Public |
| `unit` | TEXT | Unit of measure (m3, m2, kg, …) | Public |
| `price_gel` | REAL | Price in Georgian Lari | Public |
| `description` | TEXT | Optional notes | Public |
| `updated_at` | TEXT | ISO timestamp of last price update | Low |

**Source:** Seeded by `backend/database/seed_prices.py`; prices editable via `PUT /admin/materials/{id}/price`.  
**Used by:** `EstimationAgent`, MCP tool `get_material_price`, admin UI.

### 1.2 Table: `labor`

| Column | Type | Contents | Sensitivity |
|---|---|---|---|
| `id` | INTEGER PK | Auto-increment row ID | Low |
| `trade` | TEXT | Trade name (mason, electrician, …) | Public |
| `unit` | TEXT | Billing unit (day, hour) | Public |
| `price_gel` | REAL | Rate in GEL | Public |
| `description` | TEXT | Optional notes | Public |
| `updated_at` | TEXT | ISO timestamp of last price update | Low |

**Source:** Seeded by `seed_prices.py`; editable via `PUT /admin/labor/{id}/price`.  
**Used by:** MCP tool `get_labor_cost`, admin UI.

### 1.3 Table: `equipment`

| Column | Type | Contents | Sensitivity |
|---|---|---|---|
| `id` | INTEGER PK | Auto-increment row ID | Low |
| `name` | TEXT | Equipment name (crane, excavator, …) | Public |
| `unit` | TEXT | Billing unit (day, week, month) | Public |
| `price_gel` | REAL | Rental rate in GEL | Public |
| `description` | TEXT | Optional notes | Public |
| `updated_at` | TEXT | ISO timestamp of last price update | Low |

**Source:** Seeded by `seed_prices.py`.  
**Used by:** Reference data only (not yet queried by backend routes or MCP tools in v1).

### 1.4 Table: `sessions` (schema only)

| Column | Type | Contents | Sensitivity |
|---|---|---|---|
| `id` | TEXT PK | UUID session identifier | Low |
| `created_at` | TEXT | Session creation timestamp | Low |
| `image_path` | TEXT | Intended path to uploaded image | Medium |
| `estimate_json` | TEXT | Serialized cost estimate | Medium |
| `message_count` | INTEGER | Chat turn counter | Low |

**Status:** Defined in `backend/database/schema.sql` but **not written to by application code**.
Active session state lives in the in-memory store (see §2.1) instead.

---

## 2. Non-Database Storage

### 2.1 In-memory session store

**Location:** Python process heap (`backend/services/session_store.py`)  
**Key:** `session_id` (UUID from `/analyze`)

| Field | Contents | Sensitivity |
|---|---|---|
| `messages` | Chat history: system prompt + up to 40 messages (20 turns) | Medium — may contain user questions and AI answers |
| `estimate` | Cost estimate JSON returned from `/analyze` | Low |
| `created_at` | Session start timestamp | Low |

**Retention:** Until backend process restarts, or `clear_session(session_id)` is called.  
**Deletion:** Automatic on server restart; no disk persistence.

### 2.2 Uploaded building photos

**Location:** Not persisted — held in RAM for the duration of `POST /analyze` only.  
**Flow:** Image bytes → base64 → vision model → discarded after response.  
**Retention:** Request lifetime only (seconds).  
**Deletion:** Automatic when the HTTP request completes.

### 2.3 Voice audio (STT)

**Location:** Not persisted — held in RAM for the duration of `POST /transcribe` only.  
**Flow:** Audio bytes → OpenRouter Whisper API → transcript returned → bytes discarded.  
**Retention:** Request lifetime only.  
**Deletion:** Automatic when the HTTP request completes.

### 2.4 TTS audio (speak)

**Location:** Generated in memory; streamed to client as `audio/mpeg`. Not stored server-side.  
**Retention:** Request lifetime only.

### 2.5 Browser sessionStorage (frontend)

**Location:** User's browser (`frontend/lib/api.ts`)  
**Key:** `estimate_{sessionId}` — JSON copy of the cost estimate for the results page.

**Retention:** Until the browser tab is closed or sessionStorage is cleared manually.  
**Deletion:** User closes tab or clears site data in browser settings.

### 2.6 ChromaDB vector index (RAG)

**Location:** `./chroma_db/` (path configurable via `CHROMA_DB_PATH`)  
**Collection:** `construction_knowledge`

| Stored | Contents | Sensitivity |
|---|---|---|
| Embeddings | Float vectors from `openai/text-embedding-3-small` | Low |
| Document chunks | Text chunks from `rag-data/*.md` | Public |
| Metadata | Source filename per chunk | Public |

**Source:** Ingested once via `python rag-data/ingest.py`.  
**Retention:** Until directory is deleted or collection is re-ingested.  
**Deletion:** Remove `chroma_db/` directory or re-run ingest (overwrites collection).

### 2.7 Episode log (LLM + MCP metrics)

**Files:**
- `logs/episode_log.jsonl` — primary logger (`backend/services/episode_log.py`)
- `logs/episode-log.jsonl` — legacy path used by `backend/llm_client.py`
- `logs/cost-log.csv` — token/cost summary (derived from episode log writes)

| Field | Contents | PII? |
|---|---|---|
| `ts` | UTC timestamp | No |
| `type` | `llm_call` or `mcp_tool` | No |
| `session_id` | Opaque UUID (not linked to a user account) | No |
| `model`, `model_used` | Model identifier | No |
| `input_tokens`, `output_tokens` | Token counts | No |
| `latency_ms`, `cost_usd` | Performance metrics | No |
| `tool_name`, `input_hash` | MCP tool name + SHA-256 prefix of input | No raw input |
| `error` | Error message if failed | No user content |

**Retention policy:** 90 days rolling (production target).  
**Current implementation:** Append-only; no automated rotation script in repo — delete files manually or add a cron job before production deploy.

### 2.8 MCP audit log

**File:** `logs/mcp_audit.jsonl` (`mcp-server/audit_log.py`)

| Field | Contents | PII? |
|---|---|---|
| `ts` | UTC timestamp | No |
| `tool_name` | MCP tool invoked | No |
| `input_hash` | SHA-256 prefix of tool input (not raw input) | No |
| `status` | success / auth_error / error | No |
| `latency_ms` | Execution time | No |
| `error` | Sanitized error string | No |

**Retention policy:** Same as episode log (90 days target; manual deletion today).

### 2.9 Rate-limiter state

**Location:** In-memory per client IP (`backend/services/rate_limiter.py`)  
**Contents:** Timestamps of recent requests per endpoint.  
**Retention:** Rolling 60-second window; cleared on process restart.

---

## 3. Retention Summary

| Data | Storage | Retention | Deletion trigger |
|---|---|---|---|
| `materials`, `labor`, `equipment` | SQLite | Indefinite (public reference data) | Re-seed or admin price update |
| `sessions` table | SQLite | Unused | N/A |
| Chat history + estimate | In-memory (backend) | Until server restart | Process restart |
| Building photo upload | RAM (request only) | Seconds | End of `/analyze` request |
| Voice audio upload | RAM (request only) | Seconds | End of `/transcribe` request |
| TTS output | Streamed to client | Seconds | End of `/speak` request |
| Estimate copy | Browser sessionStorage | Until tab close | User closes tab |
| RAG embeddings + chunks | ChromaDB on disk | Until re-ingest | Delete `chroma_db/` or re-run ingest |
| Episode log + cost CSV | Local `logs/` | 90 days (policy); manual today | Delete log files |
| MCP audit log | Local `logs/` | 90 days (policy); manual today | Delete log files |
| Rate-limit counters | In-memory | 60 seconds | Automatic window expiry |

**No user accounts:** There is no registration, email storage, or password hashing in the current app.
Sessions are anonymous UUIDs with no link to personal identity.

---

## 4. Third-Party Data Transfers

All external AI calls go through **OpenRouter** with `"data_collection": "deny"` on every request.

| Third party | Data sent | Purpose | Notes |
|---|---|---|---|
| OpenRouter → Anthropic / Google / OpenAI models | Building photo (base64), chat messages, estimate context | Vision analysis, streaming chat, fallback chain | No account PII sent — sessions are anonymous |
| OpenRouter → `openai/text-embedding-3-small` | User chat query text (for RAG retrieval) | Query embedding | Only the query string, not full history |
| OpenRouter → `openai/whisper-1` | Audio bytes (in-memory) | Speech-to-text | Audio not stored after transcription |
| OpenRouter → `openai/tts-1` | Text to speak (estimate summary) | Text-to-speech | Text not stored server-side |

**Not sent to third parties:** Email, names, passwords, raw MCP tool inputs (only hashes logged locally).

Provider terms: [OpenRouter Privacy Policy](https://openrouter.ai/privacy) — API data not used for model training when `data_collection: deny` is set.

---

## 5. User Rights and Deletion

The app has no login system. Users exercise control as follows:

| Action | How | Effect |
|---|---|---|
| Clear chat context | Restart backend server | All in-memory sessions wiped |
| Remove estimate from browser | Close tab or clear site data | sessionStorage entry removed |
| Remove operational logs | Delete files in `logs/` | Episode and audit logs removed |
| Reset price database | Re-run `python backend/database/seed_prices.py` | Reference prices restored to seed values |
| Reset RAG index | Delete `chroma_db/` and re-run `python rag-data/ingest.py` | Vector store rebuilt |

For production (post-capstone), a privacy contact and formal deletion SLA would be added if user accounts are introduced.

---

## 6. PII Absence in Logs

Episode logs record operational metrics only — no user query text, image content, email addresses, or names.

MCP audit entries record tool name and input hash only, never raw tool arguments.

**Verification commands:**

```bash
# Should return no output (no email addresses in logs)
grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" logs/episode_log.jsonl logs/episode-log.jsonl
grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" logs/mcp_audit.jsonl

# Should return no output (no raw chat content logged)
grep -i "my name is" logs/episode_log.jsonl logs/episode-log.jsonl
```

Cross-user isolation is verified separately — see `docs/safety-audit.md`.

---

## 7. Design Review vs Implementation

The original Design Review described MongoDB Atlas, AWS S3, and Pinecone for a multi-tenant production deployment. The capstone implementation uses a **local-first** stack for demo and grading:

| Design Review target | Capstone implementation |
|---|---|
| MongoDB (user + project data) | Not implemented — no user accounts |
| AWS S3 (document storage) | Not implemented — images not persisted |
| Pinecone (vectors) | ChromaDB local directory |
| Long-term chat persistence | In-memory only (20-turn window) |

This document describes what is **actually stored today**. Production migration would require wiring the `sessions` SQLite table, adding authenticated user storage, and external object storage for uploads.

---

*Data Map · ConstructAI · CS-AI-2025 Spring 2026*
