# Case Study — ConstructAI

**Course:** CS-AI-2025 · KIU · Spring 2026
**Team:** Binary Bros & Byte Queens

---

## Problem

Georgian homebuilders receive contractor quotes with no way to verify whether the numbers are fair. A homebuilder in Kutaisi might receive three quotes for the same project — all different, none explained. There is no publicly available tool that converts a photo of a construction site into an itemized cost breakdown in Georgian Lari (GEL) based on real local market prices.

The manual alternative — hiring a cost estimator to do a quantity takeoff — takes days, costs money, and still delivers a single opinion. The result is a market where information asymmetry sits entirely with contractors, and homebuilders either overpay or abandon projects.

---

## Approach

We built ConstructAI: upload a photo of your building project, get an instant itemized estimate in GEL, then ask follow-up questions in a streaming chat.

### Architecture

The system is a two-layer pipeline:

**Layer 1 — Estimation pipeline (LangGraph)**
1. `VisionAgent` sends the image to `gemini-2.5-flash` via OpenRouter. The model returns a structured JSON list of building components with quantities and confidence levels.
2. `EstimationAgent` looks up each component in a SQLite database of Georgian market prices, multiplies quantity × unit price, and adds a 35% labor estimate. If the total exceeds 500,000 GEL, a human-review gate triggers before the result is returned.

**Layer 2 — Chat (ChatAgent)**
Follow-up questions go to `claude-3-5-haiku` via streaming SSE. The model has access to the estimate from the current session and top-3 relevant chunks from a ChromaDB vector store seeded with Georgian construction knowledge.

### Key technical decisions

- **OpenRouter as the LLM gateway** — gives us a single API key for Gemini, Claude, and GPT-4o-mini, and a clean fallback chain when rate limits hit.
- **Prompt caching** — the large system prompt (estimate JSON + RAG context) is marked `ephemeral` on every chat turn. Cache hit rate reached 93.2% in production logs, reducing cost by ~60% on cached calls.
- **In-memory session store** — avoids database writes on every chat turn. The trade-off is that sessions are lost on server restart; acceptable for a demo-stage product.
- **MCP server** — price lookups are exposed as MCP tools, enabling the agent to call them programmatically and log each call independently.

---

## Results

| Metric | Value |
|---|---|
| Golden-set accuracy | 9 / 10 (90%) |
| p95 end-to-end latency | 4.4s |
| Average cost per request | $0.0048 |
| Cache hit rate | 93.2% |
| Fallback rate | 4.5% |
| Total API spend across all development runs | $0.42 |

The app is live at **https://cost-accounting-automation.vercel.app**.

In user testing, the estimate for a 120 m² residential house in Kutaisi came within 12% of a real contractor quote — close enough to flag a 50% overcharge immediately.

---

## Lessons Learned

**Getting consistent JSON from the vision model was harder than expected.**
Low-quality or angled photos caused `gemini-2.5-flash` to return incomplete component lists or misformatted JSON. We added a `confidence` field per component and a fallback parsing path that wraps any non-JSON response in a minimal structure rather than crashing the pipeline.

**Prompt caching requires a stable system prompt.**
Early iterations rebuilt the system prompt on every request with slightly different formatting, which prevented cache hits. Fixing the template format and pinning whitespace brought the cache hit rate from ~30% to 93%.

**The 35% labor estimate is a simplification that users noticed.**
Several test users asked why labor wasn't itemized. In a production version, the EstimationAgent would query labor rates per trade from the database rather than applying a flat multiplier.

**Session memory on server restart is a real gap.**
Because sessions are in-memory, a Vercel cold start wipes all active chat sessions. We worked around this by letting the frontend re-send the estimate in the chat request body (the `estimate` field added to `ChatRequest`), so the agent can resync context even after a restart.
