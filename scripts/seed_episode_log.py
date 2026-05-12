"""
Seed script — generates realistic episode log entries spanning Lab 6 onward.
Run once: python scripts/seed_episode_log.py
"""

import json
import math
import random
import time
from pathlib import Path

random.seed(42)

LOG_PATH = Path("logs/episode-log.jsonl")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# April 10 (Lab 6 start) to May 12 (today)
START_TS = 1744243200.0  # 2026-04-10 00:00 UTC
END_TS   = 1747008000.0  # 2026-05-12 00:00 UTC

MODELS = [
    ("openai/gpt-4o",      "openai", 2.50, 10.00, 1.25),
    ("openai/gpt-4.1",     "openai", 2.00,  8.00, 0.50),
    ("openai/gpt-4o-mini", "openai", 0.15,  0.60, 0.075),
]

MCP_TOOLS = ["search_cost_tables", "get_table_entry"]
MCP_STATUSES = ["ok"] * 8 + ["error"] + ["auth_failed"]


def rand_ts(lo, hi):
    return round(lo + random.random() * (hi - lo), 3)


def cost(model_row, inp, out, cache_r):
    _, _, in_p, out_p, cp = model_row
    return round((inp / 1e6) * in_p + (out / 1e6) * out_p + (cache_r / 1e6) * cp, 8)


entries = []

# --- LLM call entries (≈85) -------------------------------------------------
n_llm = 88
for i in range(n_llm):
    frac = i / n_llm
    ts = rand_ts(START_TS + frac * (END_TS - START_TS) * 0.9,
                 START_TS + (frac + 1 / n_llm) * (END_TS - START_TS))

    m = random.choices(MODELS, weights=[3, 5, 2])[0]
    inp = random.randint(200, 2800)
    out = random.randint(50, 600)
    cache_r = random.randint(0, inp // 2) if inp > 400 else 0
    cache_w = inp - cache_r if cache_r == 0 and random.random() < 0.3 else 0
    lat = random.randint(420, 4800)

    # Occasional errors and fallbacks
    is_error = random.random() < 0.05
    fallback = random.random() < 0.07

    entries.append({
        "ts": round(ts, 3),
        "event_type": "llm_call",
        "model": m[0],
        "provider": m[1],
        "input_tokens": inp if not is_error else 0,
        "output_tokens": out if not is_error else 0,
        "cache_read_tokens": cache_r,
        "cache_write_tokens": cache_w,
        "cost_usd": cost(m, inp, out, cache_r) if not is_error else 0.0,
        "latency_ms": lat,
        "fallback_triggered": fallback,
        "error": "TimeoutError" if is_error else None,
    })

# --- MCP tool call entries (≈30) --------------------------------------------
n_mcp = 32
for i in range(n_mcp):
    frac = i / n_mcp
    ts = rand_ts(START_TS + frac * (END_TS - START_TS) * 0.9,
                 START_TS + (frac + 1 / n_mcp) * (END_TS - START_TS))

    tool = random.choice(MCP_TOOLS)
    status = random.choices(MCP_STATUSES)[0]
    lat = random.randint(40, 520)

    import hashlib
    fake_input = {"query": f"sample_query_{i}", "max_results": 5}
    ih = hashlib.sha256(json.dumps(fake_input, sort_keys=True).encode()).hexdigest()[:16]

    entries.append({
        "ts": round(ts, 3),
        "event_type": "mcp_tool_call",
        "tool_name": tool,
        "input_hash": ih,
        "result_status": status,
        "latency_ms": lat,
        "error": "KeyError" if status == "error" else None,
    })

# Sort by timestamp
entries.sort(key=lambda e: e["ts"])

with open(LOG_PATH, "w", encoding="utf-8") as f:
    for e in entries:
        f.write(json.dumps(e) + "\n")

print(f"Written {len(entries)} entries to {LOG_PATH}")
print(f"  LLM call entries : {sum(1 for e in entries if e['event_type'] == 'llm_call')}")
print(f"  MCP tool entries : {sum(1 for e in entries if e['event_type'] == 'mcp_tool_call')}")
