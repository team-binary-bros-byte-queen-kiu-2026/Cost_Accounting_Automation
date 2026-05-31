# Design Decisions — Lab 5 Sprint

**Session:** Lab 5 · April 10, 2026
**Sprint target:** Working `/analyze` endpoint that accepts an image and returns a cost estimate

## Changes from Design Review Feedback

| Feedback received | Decision | Reason |
|---|---|---|
| Architecture diagram lacked database layer | Added SQLite for price storage + sessions | Needed persistent prices across restarts |
| AI differentiator not specific enough | Added RAG (ChromaDB) as second AI layer | Semantic price retrieval > plain DB queries |
| Risk: image quality too low | Added confidence scores per line item | Makes uncertainty visible to user |

## What Stayed the Same

- Orchestrator/Specialist agent pattern (confirmed best fit)
- OpenRouter for all AI calls (flexibility + fallback)
- Next.js + FastAPI stack (team familiarity)
- Georgian Lari as primary currency

## Today's Sprint Target

**Feature:** `POST /analyze` endpoint
- Accepts: JPEG/PNG/WebP image upload
- Calls Gemini vision model to identify components
- Matches components to SQLite price database
- Returns JSON with itemized estimate and grand total

**Definition of done:** Clone fresh repo → add `.env` → `uvicorn main:app` → POST an image → receive `{session_id, estimate}` with at least one priced line item.
