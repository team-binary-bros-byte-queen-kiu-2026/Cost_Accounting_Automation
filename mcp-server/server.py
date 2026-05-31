"""
ConstructAI MCP Server — exposes price database and RAG as MCP tools.
Run: python mcp-server/server.py
Inspect: npx @modelcontextprotocol/inspector python mcp-server/server.py

Lab 6/7/8 requirements:
- Bearer token auth BEFORE tool logic
- Pydantic input validation
- JSON structured audit log
- Error sanitization
"""
import sys
import os
import time
import sqlite3
import json

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from mcp.server.fastmcp import FastMCP
from auth import verify_token
from validators import (
    GetMaterialPriceInput, GetLaborCostInput, ListPricesInput, SearchKnowledgeInput
)
from audit_log import log as audit_log
from error_handler import safe_error

DB_PATH = os.environ.get("DATABASE_PATH", "../backend/database/prices.db")

mcp = FastMCP("ConstructAI")


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# Tool 1: get_material_price
# ─────────────────────────────────────────────────────────────────────────────
@mcp.tool()
def get_material_price(material: str, unit: str = "", token: str | None = None) -> str:
    """Get the current price for a construction material from the Georgian market database."""
    t0 = time.perf_counter()
    try:
        # 1. Auth FIRST (before any logic)
        verify_token(token)

        # 2. Validate
        inp = GetMaterialPriceInput(material=material, unit=unit, token=token)

        # 3. Query
        conn = _get_db()
        rows = conn.execute(
            "SELECT * FROM materials WHERE lower(name) LIKE ? ORDER BY name LIMIT 5",
            (f"%{inp.material.lower()}%",),
        ).fetchall()
        conn.close()

        if not rows:
            result = {"found": False, "query": inp.material, "message": "No matching material found"}
        else:
            result = {
                "found": True,
                "matches": [dict(r) for r in rows],
                "currency": "GEL",
            }

        latency_ms = int((time.perf_counter() - t0) * 1000)
        audit_log("get_material_price", {"material": material}, "success", latency_ms)
        return json.dumps(result, ensure_ascii=False)

    except ValueError as e:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        audit_log("get_material_price", {"material": material}, "auth_error", latency_ms, str(e))
        return json.dumps({"error": str(e)})
    except Exception as e:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        err = safe_error(e)
        audit_log("get_material_price", {"material": material}, "error", latency_ms, err)
        return json.dumps({"error": err})


# ─────────────────────────────────────────────────────────────────────────────
# Tool 2: get_labor_cost
# ─────────────────────────────────────────────────────────────────────────────
@mcp.tool()
def get_labor_cost(trade: str, hours: float = 8.0, token: str | None = None) -> str:
    """Get labor cost for a specific trade for a given number of hours."""
    t0 = time.perf_counter()
    try:
        verify_token(token)
        inp = GetLaborCostInput(trade=trade, hours=hours, token=token)

        conn = _get_db()
        rows = conn.execute(
            "SELECT * FROM labor WHERE lower(trade) LIKE ? LIMIT 3",
            (f"%{inp.trade.lower()}%",),
        ).fetchall()
        conn.close()

        if not rows:
            result = {"found": False, "query": inp.trade, "message": "No matching trade found"}
        else:
            results = []
            for r in rows:
                row = dict(r)
                if row["unit"] == "hour":
                    total = row["price_gel"] * inp.hours
                else:  # day rate
                    total = row["price_gel"] * (inp.hours / 8)
                results.append({**row, "requested_hours": inp.hours, "estimated_total_gel": round(total, 2)})
            result = {"found": True, "matches": results, "currency": "GEL"}

        latency_ms = int((time.perf_counter() - t0) * 1000)
        audit_log("get_labor_cost", {"trade": trade, "hours": hours}, "success", latency_ms)
        return json.dumps(result, ensure_ascii=False)

    except ValueError as e:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        audit_log("get_labor_cost", {"trade": trade}, "auth_error", latency_ms, str(e))
        return json.dumps({"error": str(e)})
    except Exception as e:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        err = safe_error(e)
        audit_log("get_labor_cost", {"trade": trade}, "error", latency_ms, err)
        return json.dumps({"error": err})


# ─────────────────────────────────────────────────────────────────────────────
# Tool 3: list_prices
# ─────────────────────────────────────────────────────────────────────────────
@mcp.tool()
def list_prices(category: str = "", token: str | None = None) -> str:
    """List all construction material prices, optionally filtered by category."""
    t0 = time.perf_counter()
    try:
        verify_token(token)
        inp = ListPricesInput(category=category, token=token)

        conn = _get_db()
        if inp.category:
            rows = conn.execute(
                "SELECT * FROM materials WHERE lower(category) = ? ORDER BY name",
                (inp.category.lower(),),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM materials ORDER BY category, name").fetchall()
        conn.close()

        result = {
            "count": len(rows),
            "category_filter": inp.category or "all",
            "items": [dict(r) for r in rows],
            "currency": "GEL",
        }

        latency_ms = int((time.perf_counter() - t0) * 1000)
        audit_log("list_prices", {"category": category}, "success", latency_ms)
        return json.dumps(result, ensure_ascii=False)

    except ValueError as e:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        audit_log("list_prices", {}, "auth_error", latency_ms, str(e))
        return json.dumps({"error": str(e)})
    except Exception as e:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        err = safe_error(e)
        audit_log("list_prices", {}, "error", latency_ms, err)
        return json.dumps({"error": err})


# ─────────────────────────────────────────────────────────────────────────────
# Tool 4: search_construction_knowledge (RAG)
# ─────────────────────────────────────────────────────────────────────────────
@mcp.tool()
def search_construction_knowledge(query: str, top_k: int = 3, token: str | None = None) -> str:
    """Search the construction knowledge base using semantic similarity (RAG)."""
    t0 = time.perf_counter()
    try:
        verify_token(token)
        inp = SearchKnowledgeInput(query=query, top_k=top_k, token=token)

        # Import RAG service
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))
        from services.rag import retrieve, format_context
        chunks = retrieve(inp.query, top_k=inp.top_k)

        result = {
            "query": inp.query,
            "results_count": len(chunks),
            "results": chunks,
        }

        latency_ms = int((time.perf_counter() - t0) * 1000)
        audit_log("search_construction_knowledge", {"query": query[:50]}, "success", latency_ms)
        return json.dumps(result, ensure_ascii=False)

    except ValueError as e:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        audit_log("search_construction_knowledge", {"query": query[:50]}, "auth_error", latency_ms, str(e))
        return json.dumps({"error": str(e)})
    except Exception as e:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        err = safe_error(e)
        audit_log("search_construction_knowledge", {"query": query[:50]}, "error", latency_ms, err)
        return json.dumps({"error": err})


if __name__ == "__main__":
    mcp.run()
