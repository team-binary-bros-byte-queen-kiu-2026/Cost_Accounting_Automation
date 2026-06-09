# Model Selection — Lab 11
**Course:** CS-AI-2025 · Spring 2026  
**Team:** Binary Bros & Byte Queens  
**Benchmark data:** [`eval/model-comparison.json`](../eval/model-comparison.json)  
**Regenerate:** `python eval/run_model_comparison.py`

---

## Production model assignments

| Task | Model | Why | Fallback |
|---|---|---|---|
| Image analysis (`/analyze`) | `google/gemini-2.5-flash` | Highest golden-subset quality (8.5/10) and lowest cost ($0.02/1k calls) in benchmark; valid OpenRouter vision ID | `anthropic/claude-3-5-haiku` → `openai/gpt-4o-mini` |
| Streaming chat (`/chat/stream`) | `anthropic/claude-3-5-haiku` | Strong instruction following for short GEL answers; stable p95 ~2.5s | `SECONDARY_MODEL` → `OSS_FALLBACK` |
| RAG embeddings | `openai/text-embedding-3-small` | Good domain similarity, $0.02/M tokens | none (ChromaDB local) |
| Text-to-speech (`/speak`) | `openai/tts-1` | Low-latency speech via OpenRouter | HTTP 502 |
| Speech-to-text (`/transcribe`) | `openai/whisper-1` | Accurate transcription | HTTP 502 |

Models are configured via environment variables in `backend/settings.py`:

```bash
PRIMARY_MODEL=anthropic/claude-3-5-haiku
SECONDARY_MODEL=anthropic/claude-3-5-haiku
OSS_FALLBACK=openai/gpt-4o-mini
PRIMARY_VISION_MODEL=google/gemini-2.5-flash
```

---

## Benchmark results (Jun 9 2026)

Methodology: 4 golden-set questions (`factual_1`, `reasoning_1`, `refusal_1`, `format_1`), **5 runs each** (20 calls per model), scored with the same rules as `eval/run_eval.py`. All requests include `data_collection: deny`.

| Model | Selected? | Quality (0–10) | Latency p50 | Latency p95 | Cost / 1k req | Failure rate |
|---|---|---|---|---|---|---|
| `anthropic/claude-3-5-haiku` | ✅ chat primary | 6.5 | 2,116 ms | 2,536 ms | $0.36 | 0% |
| `google/gemini-2.5-flash` | ✅ vision primary | 8.5 | 945 ms | 4,265 ms | $0.02 | 0% |
| `openai/gpt-4o-mini` | ✅ OSS fallback | 7.5 | 1,005 ms | 1,736 ms | $0.03 | 0% |
| `openai/o3-mini` | ❌ rejected | 7.0 | 3,224 ms | 4,122 ms | $1.67 | 0% |

**Decision:** Haiku for chat (reliability + predictable latency). Gemini 2.5 Flash for vision (best quality/cost). GPT-4o-mini as cheap fallback. o3-mini rejected despite decent quality — **3× higher p50 latency** and **~80× higher cost** than Flash.

> Note: `google/gemini-3-flash` is **not a valid OpenRouter model ID** (returns HTTP 400). Production uses `google/gemini-2.5-flash`.

---

## Why we did not use o3 / o3-mini for chat

OpenAI o3-family models prioritize deep reasoning over speed. In our benchmark, o3-mini p50 latency was **3,224 ms** vs **945–2,116 ms** for Flash/Haiku. ConstructAI streams chat responses and targets sub-3 s UX; o3-mini also costs **$1.67 per 1,000 requests** vs **$0.02–0.36** for selected models.

We did not use full **o3** for the same reason (checklist cites 8–15 s latency).

---

## Why we did not use Claude Sonnet 4.6 as primary

Claude Sonnet 4.6 offers higher reasoning quality but at roughly **4–8× the token cost** of Haiku. For short cost-estimation Q&A (2–4 sentences, GEL figures), Haiku meets quality needs at lower spend. Sonnet remains a viable upgrade if answer depth requirements increase.

---

## Fallback strategy

```
PRIMARY_MODEL (Haiku)
    → SECONDARY_MODEL (Haiku — rate-limit failover)
        → OSS_FALLBACK (gpt-4o-mini)
            → SSE error event (no raw traceback)
```

Vision pipeline uses `FALLBACK_CHAIN`: `PRIMARY_VISION_MODEL → SECONDARY_MODEL → OSS_FALLBACK`.

Implementation: `backend/services/openrouter.py` — `chat_with_fallback()`, `stream_chat()`, tenacity retry on 5xx/timeouts.

---

## Cost analysis (production logs)

From episode logs (153 entries) — full metrics in [`docs/metrics-report.md`](metrics-report.md):

| Task | Model | Est. cost / call | Est. cost / 1k calls |
|---|---|---|---|
| Image analysis | gemini-2.5-flash | ~$0.00036 | ~$0.36 |
| Chat response | claude-3-5-haiku | ~$0.0036 | ~$3.60 |
| Embedding | text-embedding-3-small | ~$0.000006 | ~$0.006 |

**Total logged LLM spend:** ~$0.44 · **Cache hit rate:** 67.8% · **Golden eval pass rate:** 7/10 (70%)

---

## Privacy / data handling

- All OpenRouter requests set `"data_collection": "deny"` (GDPR opt-out).
- Requests route through OpenRouter infrastructure — see [`docs/safety-audit.md`](safety-audit.md) § Data Governance.
- No user message content is written to the episode log (tokens/costs/latency only).

---

## How to reproduce the benchmark

```bash
export OPENROUTER_API_KEY=your_key   # or set in .env
python eval/run_model_comparison.py
```

Output: `eval/model-comparison.json`
