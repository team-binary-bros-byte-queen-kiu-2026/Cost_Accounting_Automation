"""
JSONL episode logger — records every LLM call and MCP tool call.
Required for Lab 6+ and Safety Audit Area 1 (100+ entries).
"""
import json
import os
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(os.environ.get("EPISODE_LOG_PATH", "./logs/episode_log.jsonl"))
COST_LOG_PATH = Path(os.environ.get("COST_LOG_PATH", "./logs/cost-log.csv"))


def _ensure_files():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not COST_LOG_PATH.exists():
        COST_LOG_PATH.write_text(
            "timestamp,session_id,model,input_tokens,output_tokens,latency_ms,cost_usd\n"
        )


def log_llm_call(
    session_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    cost_usd: float,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
    fallback_triggered: bool = False,
    model_used: str = "",
    error: str | None = None,
):
    _ensure_files()
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "llm_call",
        "session_id": session_id,
        "model": model,
        "model_used": model_used or model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "cost_usd": round(cost_usd, 8),
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": cache_write_tokens,
        "fallback_triggered": fallback_triggered,
        "error": error,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Also write to cost-log.csv
    with open(COST_LOG_PATH, "a") as f:
        f.write(
            f"{entry['ts']},{session_id},{model_used or model},"
            f"{input_tokens},{output_tokens},{latency_ms},{entry['cost_usd']}\n"
        )


def log_mcp_call(
    session_id: str,
    tool_name: str,
    input_data: dict,
    status: str,
    latency_ms: int,
    error: str | None = None,
):
    _ensure_files()
    input_hash = hashlib.sha256(json.dumps(input_data, sort_keys=True).encode()).hexdigest()[:12]
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "mcp_tool",
        "session_id": session_id,
        "tool_name": tool_name,
        "input_hash": input_hash,
        "status": status,
        "latency_ms": latency_ms,
        "error": error,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def count_entries() -> int:
    if not LOG_PATH.exists():
        return 0
    return sum(1 for _ in open(LOG_PATH))
