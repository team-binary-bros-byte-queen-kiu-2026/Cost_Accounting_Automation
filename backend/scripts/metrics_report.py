"""
Compute capstone metrics from episode logs and eval results.
Writes docs/metrics-report.md.

Usage (from repo root):
    python backend/scripts/metrics_report.py
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_PATHS = [
    REPO_ROOT / "logs" / "episode-log.jsonl",
    REPO_ROOT / "logs" / "episode_log.jsonl",
]
EVAL_RESULTS_PATH = REPO_ROOT / "eval" / "results" / "latest.json"
OUTPUT_PATH = REPO_ROOT / "docs" / "metrics-report.md"

THRESHOLDS = {
    "total_entries": 100,
    "avg_latency_ms": 5000,
    "cache_hit_rate_pct": 30,
    "fallback_rate_pct": 10,
    "error_rate_pct": 5,
    "eval_pass_rate_pct": 70,
}


def load_entries() -> list[dict]:
    entries: list[dict] = []
    for path in LOG_PATHS:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def entry_type(entry: dict) -> str:
    return entry.get("event_type") or entry.get("type") or ""


def is_llm_call(entry: dict) -> bool:
    return entry_type(entry) == "llm_call"


def is_mcp_call(entry: dict) -> bool:
    t = entry_type(entry)
    return t in ("mcp_tool_call", "mcp_tool")


def has_error(entry: dict) -> bool:
    err = entry.get("error")
    if err is None:
        return False
    if is_mcp_call(entry):
        return entry.get("result_status") == "error" or entry.get("status") == "error" or bool(err)
    return bool(err)


def compute_metrics(entries: list[dict]) -> dict:
    llm_calls = [e for e in entries if is_llm_call(e)]
    latencies = [e["latency_ms"] for e in llm_calls if isinstance(e.get("latency_ms"), (int, float))]
    cache_hits = [e for e in llm_calls if e.get("cache_read_tokens", 0) > 0]
    cache_misses = [e for e in llm_calls if e.get("cache_read_tokens", 0) == 0]
    fallbacks = [e for e in llm_calls if e.get("fallback_triggered")]
    errors = [e for e in entries if has_error(e)]
    total_cost = sum(e.get("cost_usd", 0) or 0 for e in llm_calls)

    cache_hit_rate = (len(cache_hits) / len(llm_calls) * 100) if llm_calls else 0.0
    fallback_rate = (len(fallbacks) / len(llm_calls) * 100) if llm_calls else 0.0
    error_rate = (len(errors) / len(entries) * 100) if entries else 0.0
    avg_latency = statistics.mean(latencies) if latencies else 0.0
    median_latency = statistics.median(latencies) if latencies else 0.0

    def group_stats(group: list[dict]) -> dict:
        lats = [e["latency_ms"] for e in group if isinstance(e.get("latency_ms"), (int, float))]
        costs = [e.get("cost_usd", 0) or 0 for e in group]
        return {
            "count": len(group),
            "median_latency_ms": round(statistics.median(lats), 1) if lats else 0.0,
            "total_cost_usd": round(sum(costs), 6),
        }

    eval_pass_rate = None
    eval_passed = None
    eval_total = None
    if EVAL_RESULTS_PATH.exists():
        eval_data = json.loads(EVAL_RESULTS_PATH.read_text(encoding="utf-8"))
        eval_passed = eval_data.get("passed")
        eval_total = eval_data.get("total")
        if eval_data.get("pass_rate") is not None:
            eval_pass_rate = eval_data["pass_rate"] * 100
        elif eval_passed is not None and eval_total:
            eval_pass_rate = eval_passed / eval_total * 100

    return {
        "total_entries": len(entries),
        "llm_calls": len(llm_calls),
        "mcp_calls": len([e for e in entries if is_mcp_call(e)]),
        "avg_latency_ms": round(avg_latency, 1),
        "median_latency_ms": round(median_latency, 1),
        "cache_hit_rate_pct": round(cache_hit_rate, 1),
        "fallback_rate_pct": round(fallback_rate, 1),
        "error_rate_pct": round(error_rate, 1),
        "total_cost_usd": round(total_cost, 4),
        "cache_miss": group_stats(cache_misses),
        "cache_hit": group_stats(cache_hits),
        "eval_pass_rate_pct": round(eval_pass_rate, 1) if eval_pass_rate is not None else None,
        "eval_passed": eval_passed,
        "eval_total": eval_total,
    }


def status(passed: bool) -> str:
    return "✅" if passed else "❌"


def render_report(metrics: dict) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    eval_value = (
        f"{metrics['eval_passed']}/{metrics['eval_total']} ({metrics['eval_pass_rate_pct']}%)"
        if metrics["eval_pass_rate_pct"] is not None
        else "— (run eval/run_eval.py)"
    )

    rows = [
        ("Total log entries", str(metrics["total_entries"]), f"≥ {THRESHOLDS['total_entries']}",
         metrics["total_entries"] >= THRESHOLDS["total_entries"]),
        ("Avg LLM latency (ms)", str(metrics["avg_latency_ms"]), f"≤ {THRESHOLDS['avg_latency_ms']}",
         metrics["avg_latency_ms"] <= THRESHOLDS["avg_latency_ms"]),
        ("Cache hit rate", f"{metrics['cache_hit_rate_pct']}%", f"≥ {THRESHOLDS['cache_hit_rate_pct']}%",
         metrics["cache_hit_rate_pct"] >= THRESHOLDS["cache_hit_rate_pct"]),
        ("Fallback rate", f"{metrics['fallback_rate_pct']}%", f"≤ {THRESHOLDS['fallback_rate_pct']}%",
         metrics["fallback_rate_pct"] <= THRESHOLDS["fallback_rate_pct"]),
        ("Error rate", f"{metrics['error_rate_pct']}%", f"≤ {THRESHOLDS['error_rate_pct']}%",
         metrics["error_rate_pct"] <= THRESHOLDS["error_rate_pct"]),
        ("Eval pass rate", eval_value, f"≥ {THRESHOLDS['eval_pass_rate_pct']}%",
         metrics["eval_pass_rate_pct"] is not None and metrics["eval_pass_rate_pct"] >= THRESHOLDS["eval_pass_rate_pct"]),
    ]

    table_lines = ["| Metric | Value | Threshold | Status |", "|---|---|---|---|"]
    for name, value, threshold, ok in rows:
        table_lines.append(f"| {name} | {value} | {threshold} | {status(ok)} |")

    miss = metrics["cache_miss"]
    hit = metrics["cache_hit"]
    latency_change = 0.0
    if miss["median_latency_ms"] > 0 and hit["count"] > 0:
        latency_change = round(
            (miss["median_latency_ms"] - hit["median_latency_ms"]) / miss["median_latency_ms"] * 100,
            1,
        )

    log_files = "\n".join(
        f"- `{p.relative_to(REPO_ROOT)}` ({'found' if p.exists() else 'missing'})"
        for p in LOG_PATHS
    )
    eval_file = f"- `{EVAL_RESULTS_PATH.relative_to(REPO_ROOT)}` ({'found' if EVAL_RESULTS_PATH.exists() else 'missing'})"

    return f"""# Metrics Report — Lab 9
**Generated by:** `backend/scripts/metrics_report.py`
**Generated at:** {generated}
**Sources:** `logs/episode-log.jsonl`, `logs/episode_log.jsonl`, `eval/results/latest.json`

Run `python backend/scripts/metrics_report.py` from the repo root to regenerate.

## Summary

- LLM calls analysed: **{metrics['llm_calls']}**
- MCP tool calls analysed: **{metrics['mcp_calls']}**
- Total logged cost (LLM): **${metrics['total_cost_usd']}**
- Median LLM latency: **{metrics['median_latency_ms']} ms**

## Six Required Metrics

{chr(10).join(table_lines)}

## Caching Impact (from episode log)

Compared calls **without** cache reads (cache miss / first call) vs **with** cache reads (cache hit):

| Group | Calls | Median latency (ms) | Total cost (USD) |
|---|---|---|---|
| Cache miss (no `cache_read_tokens`) | {miss['count']} | {miss['median_latency_ms']} | {miss['total_cost_usd']} |
| Cache hit (`cache_read_tokens` > 0) | {hit['count']} | {hit['median_latency_ms']} | {hit['total_cost_usd']} |

Median latency change (miss → hit): **{latency_change}%** (negative = cached calls were slower on average, often due to longer sessions).

Prompt caching is enabled via `cache_control: {{"type": "ephemeral"}}` on the system prompt in `backend/services/openrouter.py`.

## Log Files Read

{log_files}
{eval_file}
"""


def main():
    entries = load_entries()
    if not entries:
        raise SystemExit("No episode log entries found. Check logs/episode-log.jsonl or logs/episode_log.jsonl.")

    metrics = compute_metrics(entries)
    report = render_report(metrics)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"Metrics report written to {OUTPUT_PATH}")
    print(f"  Total entries: {metrics['total_entries']}")
    print(f"  Cache hit rate: {metrics['cache_hit_rate_pct']}%")
    print(f"  Eval pass rate: {metrics['eval_pass_rate_pct']}%")


if __name__ == "__main__":
    main()
