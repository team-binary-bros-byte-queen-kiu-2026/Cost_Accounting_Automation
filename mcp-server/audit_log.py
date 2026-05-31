"""
JSON structured audit log for MCP tool calls.
Lab 8: tool_name, input_hash, execution_status, latency_ms.
"""
import json
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(os.environ.get("MCP_AUDIT_LOG", "../logs/mcp_audit.jsonl"))


def log(tool_name: str, input_data: dict, status: str, latency_ms: int, error: str | None = None):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    input_hash = hashlib.sha256(json.dumps(input_data, sort_keys=True).encode()).hexdigest()[:12]
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "input_hash": input_hash,
        "status": status,
        "latency_ms": latency_ms,
        "error": error,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
