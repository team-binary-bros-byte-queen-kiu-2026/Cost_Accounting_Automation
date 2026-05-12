"""
Cost Accounting Automation — Production MCP Server
CS-AI-2025 Lab 8, Spring 2026

Tools:
  search_cost_tables  — Semantic search over construction cost reference tables
  get_table_entry     — Retrieve a specific table entry by code

All four production layers applied:
  1. Bearer token authentication
  2. Pydantic input validation
  3. Structured JSON audit logging
  4. Sanitised error responses (no tracebacks to caller)

Usage:
    pip install mcp pydantic python-dotenv
    MCP_SECRET_KEY=your_secret python mcp-server/server.py
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field, ValidationError

# ─── Configuration ─────────────────────────────────────────────────────────

MCP_SECRET = os.environ.get("MCP_SECRET_KEY", "")
LOG_PATH = Path(os.environ.get("MCP_LOG_PATH", "logs/mcp-audit.jsonl"))

logging.basicConfig(level=logging.INFO)
server_logger = logging.getLogger("mcp-server")

# ─── Auth ──────────────────────────────────────────────────────────────────

def verify_token(token: str) -> bool:
    """Constant-time comparison prevents timing attacks."""
    if not MCP_SECRET:
        server_logger.warning("MCP_SECRET_KEY not set — all requests rejected")
        return False
    if not token:
        return False
    return hmac.compare_digest(MCP_SECRET.encode(), token.encode())


def error_response(message: str) -> list[TextContent]:
    """Return a structured error — never a traceback."""
    return [TextContent(type="text", text=json.dumps({"error": message}))]


# ─── Audit Logger ──────────────────────────────────────────────────────────

def log_tool_call(
    tool_name: str,
    input_dict: dict,
    result_status: str,
    latency_ms: int,
    error: str = None,
) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    input_hash = hashlib.sha256(
        json.dumps(input_dict, sort_keys=True).encode()
    ).hexdigest()[:16]
    entry = {
        "ts": round(time.time(), 3),
        "event_type": "mcp_tool_call",
        "tool_name": tool_name,
        "input_hash": input_hash,
        "result_status": result_status,
        "latency_ms": latency_ms,
        "error": error,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    level = logging.ERROR if result_status == "error" else logging.INFO
    server_logger.log(
        level,
        f"tool={tool_name} status={result_status} latency={latency_ms}ms"
        + (f" error={error}" if error else ""),
    )


# ─── Input Schemas ─────────────────────────────────────────────────────────

class SearchCostTablesInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=600,
                       description="Natural language search query about construction costs")
    max_results: int = Field(default=5, ge=1, le=20,
                             description="Number of results to return (1-20)")
    table_category: str = Field(default="all",
                                description="Filter by category: materials | labour | overhead | all")

    class Config:
        populate_by_name = True


class GetTableEntryInput(BaseModel):
    code: str = Field(..., min_length=2, max_length=50,
                      description="Table entry code, e.g. НР-123 or FER-2001-01-001")

    class Config:
        populate_by_name = True


# ─── MCP Server ────────────────────────────────────────────────────────────

app = Server("cost-accounting-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_cost_tables",
            description=(
                "Semantic search over Georgian construction cost reference tables. "
                "Returns relevant entries matching the query including cost codes, "
                "material rates, labour norms, and overhead coefficients."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "_auth_token": {"type": "string", "description": "Bearer auth token"},
                    "query": {"type": "string", "description": "Search query (max 600 chars)"},
                    "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
                    "table_category": {
                        "type": "string",
                        "enum": ["materials", "labour", "overhead", "all"],
                        "default": "all",
                    },
                },
                "required": ["_auth_token", "query"],
            },
        ),
        Tool(
            name="get_table_entry",
            description=(
                "Retrieve a specific construction cost table entry by its code. "
                "Returns the full entry including unit, rate, and applicable regulations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "_auth_token": {"type": "string", "description": "Bearer auth token"},
                    "code": {"type": "string", "description": "Table code, e.g. НР-123"},
                },
                "required": ["_auth_token", "code"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    start = time.time()

    # ── Layer 1: Authentication ───────────────────────────────────────────
    token = arguments.pop("_auth_token", "")
    if not verify_token(token):
        log_tool_call(name, {}, "auth_failed", round((time.time() - start) * 1000))
        return error_response("unauthorized")

    # ── Layer 2: Input Validation + Layer 3/4: Execute ────────────────────
    if name == "search_cost_tables":
        try:
            validated = SearchCostTablesInput(**arguments)
        except ValidationError as e:
            log_tool_call(name, arguments, "validation_failed",
                          round((time.time() - start) * 1000),
                          f"{e.error_count()} validation errors")
            return error_response("invalid_input")

        try:
            result = await do_search(validated.query, validated.max_results, validated.table_category)
            latency_ms = round((time.time() - start) * 1000)
            log_tool_call(name, validated.model_dump(), "ok", latency_ms)
            return [TextContent(type="text", text=json.dumps(result))]
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000)
            server_logger.error(f"Tool {name} failed: {e}", exc_info=True)
            log_tool_call(name, validated.model_dump(), "error", latency_ms, type(e).__name__)
            return error_response("tool_execution_failed")

    elif name == "get_table_entry":
        try:
            validated = GetTableEntryInput(**arguments)
        except ValidationError as e:
            log_tool_call(name, arguments, "validation_failed",
                          round((time.time() - start) * 1000),
                          f"{e.error_count()} validation errors")
            return error_response("invalid_input")

        try:
            result = await do_get_entry(validated.code)
            latency_ms = round((time.time() - start) * 1000)
            log_tool_call(name, validated.model_dump(), "ok", latency_ms)
            return [TextContent(type="text", text=json.dumps(result))]
        except Exception as e:
            latency_ms = round((time.time() - start) * 1000)
            server_logger.error(f"Tool {name} failed: {e}", exc_info=True)
            log_tool_call(name, validated.model_dump(), "error", latency_ms, type(e).__name__)
            return error_response("tool_execution_failed")

    return error_response("unknown_tool")


# ─── Tool Logic (replace with real Pinecone / MongoDB calls) ───────────────

async def do_search(query: str, max_results: int, category: str) -> dict:
    """
    Placeholder — replace with real Pinecone similarity search.
    In production: embed query with text-embedding-3-large, query Pinecone,
    return top-k chunks with metadata from MongoDB.
    """
    return {
        "results": [
            {
                "code": "FER-2001-01-001",
                "description": f"Reference entry matching: {query}",
                "unit": "m3",
                "rate_gel": 124.50,
                "category": category if category != "all" else "materials",
                "score": 0.92,
            }
        ][:max_results],
        "query": query,
        "category": category,
        "total_found": 1,
    }


async def do_get_entry(code: str) -> dict:
    """
    Placeholder — replace with MongoDB lookup by code.
    """
    return {
        "code": code,
        "description": f"Construction cost entry {code}",
        "unit": "m3",
        "rate_gel": 98.00,
        "overhead_coefficient": 1.18,
        "regulation": "Georgian Construction Norms 2019",
        "last_updated": "2024-01-01",
    }


# ─── Entry Point ──────────────────────────────────────────────────────────

async def main():
    if not MCP_SECRET:
        print("WARNING: MCP_SECRET_KEY not set. Set it before running in production.")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
