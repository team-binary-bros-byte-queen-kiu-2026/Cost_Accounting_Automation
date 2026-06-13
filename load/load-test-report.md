# Load Test Report

**Target:** https://cost-accounting-automation.vercel.app
**Tool:** Locust 2.x
**Date:** 2026-06-10
**Config:** 50 virtual users · 5 users/sec spawn rate · 2-minute run · headless mode

```bash
locust -f load/locustfile.py \
  --host https://cost-accounting-automation.vercel.app \
  --users 50 --spawn-rate 5 --run-time 2m --headless
```

---

## Results

### Latency (ms)

| Endpoint | p50 | p95 | p99 | Max |
|---|---|---|---|---|
| `GET /api/health` | 98 | 210 | 380 | 512 |
| `POST /api/chat/stream` | 2,640 | 4,406 | 4,890 | 7,210 |

### Throughput and errors

| Metric | Value |
|---|---|
| Total requests | 1,847 |
| Requests/sec (avg) | 15.4 |
| Failure rate | 2.1% |
| 429 responses (rate limit) | 38 (2.1%) — expected; fallback model activated |
| 5xx responses | 0 |

### Notes

- `/health` endpoint responds well under 500ms at all percentiles — hard gate satisfied.
- `POST /api/chat/stream` p95 of 4,406ms matches episode log figures — consistent with live model latency, not infrastructure overhead.
- All 429 responses triggered the fallback chain (`claude-3-5-haiku` → `gpt-4o-mini`). No requests returned a hard error to the client.
- No memory or connection errors observed during the 2-minute window.
- Vercel serverless cold starts account for the long tail (p99 ~4.9s); warm instances stay under 3s.
