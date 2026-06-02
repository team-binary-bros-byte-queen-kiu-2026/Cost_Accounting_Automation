# Optimization Report — Prompt Caching Benchmark
**Lab 8 · CS-AI-2025 · Spring 2026**

## What was cached

The `ChatAgent` system prompt contains the full estimate JSON + RAG context, typically 1,800–2,400 tokens.
This is marked with `"cache_control": {"type": "ephemeral"}` on the system message.

## Benchmark Results

*(Run 10 calls without caching, then 10 calls with caching. Replace with actual numbers.)*

| Run | Mode | Latency (ms) | Input tokens | Cache read | Cost (USD) |
|-----|------|-------------|--------------|-----------|------------|
| 1  | no-cache | — | — | 0 | — |
| ... | | | | | |
| 11 | cached | — | — | ~2000 | — |
| ... | | | | | |

**Median latency without caching:** __ ms
**Median latency with caching:** __ ms
**Latency reduction:** __%

**Cost without caching (10 calls):** $___
**Cost with caching (10 calls):** $___
**Cost reduction:** __%

## OpenRouter Fallback Chain

Configured in `backend/services/openrouter.py`:

1. PRIMARY: `anthropic/claude-3-5-haiku`
2. SECONDARY: `openai/gpt-4o-mini`
3. TERTIARY: `google/gemini-2.0-flash`

Fallback triggers on `RateLimitError` (HTTP 429) or `APIStatusError` (HTTP 5xx).
`fallback_triggered: true` logged in episode log when fallback activates.
