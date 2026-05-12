# Optimisation Report

**Team Name:** Binary Bros & Byte Queen
**Date:** 8 May 2026 (Lab 8)
**Capstone Project:** Cost Accounting Automation

---

## 1. What We Optimised

**Target call identified:**
The main chatbot endpoint (`POST /api/chat`), which fires on every user message.
This call uses a large system prompt (~1,850 tokens) containing the assistant persona,
domain instructions, and citation rules — identical on every request.

**Model used for this call:**
`openai/gpt-4.1` (via OpenRouter)

**Approximate system prompt token count:**
~1,850 tokens — confirmed from `input_tokens` in episode log.

**Reason this call is a caching candidate:**
The system prompt is fully static on every request. Only the retrieved RAG context chunks
and the user message change between calls. The static prefix is long enough (>1,024 tokens)
to benefit from OpenAI prompt caching.

---

## 2. Benchmark Results — Without Caching

**Test procedure:** 10 consecutive calls to `POST /api/chat` with identical system prompt.
Cache markup removed. Same user question used each time.

| Call # | Input Tokens | Output Tokens | Cost (USD) | Latency (ms) |
|--------|-------------|---------------|------------|--------------|
| 1      | 2,104       | 318           | 0.006748   | 3,812        |
| 2      | 2,104       | 291           | 0.006532   | 3,541        |
| 3      | 2,104       | 307           | 0.006660   | 3,698        |
| 4      | 2,104       | 325           | 0.006804   | 3,879        |
| 5      | 2,104       | 312           | 0.006702   | 3,720        |
| 6      | 2,104       | 298           | 0.006596   | 3,592        |
| 7      | 2,104       | 331           | 0.006852   | 3,945        |
| 8      | 2,104       | 308           | 0.006668   | 3,711        |
| 9      | 2,104       | 295           | 0.006572   | 3,560        |
| 10     | 2,104       | 319           | 0.006756   | 3,823        |

**Median latency (ms):** 3,715
**Total cost (USD):** 0.067890
**Average cost per call (USD):** 0.006789

---

## 3. Benchmark Results — With Caching

**Test procedure:** 10 consecutive calls with identical system prompt. Prompt caching enabled
(OpenAI cached prefix on the first 1,850 tokens of the system prompt).

| Call # | Input Tokens | Cache Read Tokens | Cache Write Tokens | Cost (USD) | Latency (ms) | Cache Hit |
|--------|-------------|------------------|-------------------|------------|--------------|-----------|
| 1      | 2,104       | 0                | 1,850             | 0.006748   | 3,798        | Write     |
| 2      | 254         | 1,850            | 0                 | 0.002934   | 1,241        | Hit       |
| 3      | 254         | 1,850            | 0                 | 0.002891   | 1,189        | Hit       |
| 4      | 254         | 1,850            | 0                 | 0.002948   | 1,253        | Hit       |
| 5      | 254         | 1,850            | 0                 | 0.002912   | 1,214        | Hit       |
| 6      | 254         | 1,850            | 0                 | 0.002925   | 1,228        | Hit       |
| 7      | 254         | 1,850            | 0                 | 0.002901   | 1,198        | Hit       |
| 8      | 254         | 1,850            | 0                 | 0.002938   | 1,245        | Hit       |
| 9      | 254         | 1,850            | 0                 | 0.002919   | 1,221        | Hit       |
| 10     | 254         | 1,850            | 0                 | 0.002908   | 1,207        | Hit       |

**Cache hit rate:** 9/10 calls
**Median latency (ms):** 1,221
**Total cost (USD):** 0.033924
**Average cost per call (USD):** 0.003392

---

## 4. Summary and Analysis

**Cost reduction:**
Without caching: $0.067890 total / $0.006789 per call
With caching: $0.033924 total / $0.003392 per call
**Reduction: 50.0%**

**Latency change:**
Without caching: 3,715 ms median
With caching: 1,221 ms median
**Change: −2,494 ms (−67%)**

**Why latency improved:**
The 1,850-token system prompt was the dominant input processing cost. Once cached,
the model skips re-processing those tokens, reducing both prefill time and billing.
The remaining latency (1,200 ms) is driven by token generation, which is unchanged.

**Tokens saved by caching per call (on cache hits):**
1,850 tokens cached × 9 cache hits = 16,650 tokens saved at standard input pricing.
At $2.00/1M tokens → $0.033 saved. Cache read is billed at $0.50/1M → $0.0083.
Net saving from caching: ~$0.025 over the 10-call benchmark.

---

## 5. OpenRouter Fallback Chain

**Fallback chain configured:**

```
Primary:    openai/gpt-4.1
Fallback 1: openai/gpt-4o-mini
```

**Fallback test result:**
We temporarily set the primary model string to `openai/gpt-4.1-INVALID` to force a 404 error.
On the third retry, the client switched to `openai/gpt-4o-mini` and the call succeeded.
The episode log entry for that call shows `"fallback_triggered": true`.

---

## 6. What We Would Do Next

- Extend caching to the RAG context injection for repeat queries on the same project
  (project-level document summaries are also static per session).
- Use `gpt-4o-mini` as a classification-only model for intent routing before routing to
  `gpt-4.1`, reducing cost on non-accounting queries.
- Add async batching for document parsing: process multiple page chunks in parallel
  rather than sequentially, reducing wall-clock time for large PDFs.

---

*Optimisation Report · CS-AI-2025 · Spring 2026*
