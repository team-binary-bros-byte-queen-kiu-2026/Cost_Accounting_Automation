# Generation Strategy

**Project:** Cost Accounting Automation
**Lab:** 3 — Design Review Sprint

This document describes how our application uses AI generation capabilities.

---

## Primary Generation Approach

We use AI generation in two distinct workflows:

**1. Table-to-database conversion (offline / admin pipeline)**
An AI agent (GPT-4o) analyses each legacy construction reference table and generates a tailored Python/Node.js conversion script that maps the table's specific structure into our unified MongoDB schema. This is a code-generation task — the model generates executable transformation logic rather than user-facing text. The output is reviewed before execution.

**2. Conversational chatbot (user-facing, real-time)**
A RAG pipeline retrieves the top-k most relevant reference table chunks from Pinecone (using text-embedding-3-large embeddings), then passes them as grounded context to GPT-4.1. The model generates a precise, cited answer to the user's accounting question. Responses are streamed token-by-token to the frontend.

---

## Models Used

| Purpose | Model | Provider |
|---|---|---|
| Document parsing & structured data extraction | GPT-4o | OpenAI via OpenRouter |
| Chatbot Q&A (RAG) | GPT-4.1 | OpenAI via OpenRouter |
| Semantic embeddings for vector search | text-embedding-3-large | OpenAI |
| Voice query transcription | Whisper-1 | OpenAI |
| Fallback (low-stakes / unavailable primary) | GPT-4o-mini | OpenAI via OpenRouter |

---

## Prompt Strategy

**Document parsing (Flow 1):**
- System prompt instructs the model to extract fields as a strict JSON schema.
- Few-shot examples of input/output pairs are prepended for table types seen during development.
- Temperature: 0.0 — deterministic output required for structured data extraction.

**Chatbot (Flow 2 — RAG):**
- System prompt restricts the model to the domain ("answer only based on the provided context; cite the table name or regulation code; if the answer is not present, say so explicitly").
- Retrieved Pinecone chunks are inserted as numbered context blocks between `[CONTEXT START]` and `[CONTEXT END]` delimiters.
- User question is appended as the human turn.
- Temperature: 0.2 — low variance for factual professional Q&A.
- No chain-of-thought shown to user; model is instructed to produce a direct answer followed by citations.

---

## Output Format

**Document parsing:**
Model returns a JSON object matching the predefined MongoDB schema for that document type. The backend validates the JSON against the schema before writing to the database. If validation fails, the job is flagged for manual review.

**Chatbot:**
Model returns plain prose with inline citation markers (e.g., "Table НР-123, Section 4.2"). The frontend citation parser extracts these markers and renders them as linked footnotes pointing to the source table entry in the database. Responses are streamed; citations are resolved after the stream completes.
