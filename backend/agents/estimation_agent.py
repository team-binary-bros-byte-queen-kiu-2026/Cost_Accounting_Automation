"""
Estimation specialist agent.
Takes identified components → queries MCP price tools → returns cost estimate.
"""
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../mcp-server"))

from .state import AgentState
from ..database import db
from ..services import episode_log
import time

LARGE_ESTIMATE_THRESHOLD = 500_000  # GEL — triggers approval gate


def _lookup_price(component_name: str, category: str) -> dict | None:
    """Direct DB lookup (backend-side tool call, also logged as MCP call)."""
    t0 = time.perf_counter()
    result = db.get_material_by_name(component_name)
    if not result:
        result = db.get_materials_by_category(category)
        result = result[0] if result else None
    latency_ms = int((time.perf_counter() - t0) * 1000)
    episode_log.log_mcp_call(
        session_id="estimation",
        tool_name="get_material_price",
        input_data={"material": component_name, "category": category},
        status="success" if result else "not_found",
        latency_ms=latency_ms,
    )
    return result


def estimation_node(state: AgentState) -> AgentState:
    """LangGraph node: price each component and produce itemized estimate."""
    components_data = state.get("identified_components", {})
    components = components_data.get("components", [])
    session_id = state["session_id"]

    line_items = []
    total_gel = 0.0

    for comp in components:
        price_row = _lookup_price(comp["name"], comp.get("category", ""))
        if price_row:
            unit_price = price_row["price_gel"]
            quantity = comp.get("estimated_quantity", 1)
            subtotal = unit_price * quantity
            line_items.append({
                "name": comp["name"],
                "category": comp.get("category", ""),
                "quantity": quantity,
                "unit": price_row["unit"],
                "unit_price_gel": unit_price,
                "subtotal_gel": round(subtotal, 2),
                "confidence": comp.get("confidence", "medium"),
                "notes": comp.get("notes", ""),
                "matched_item": price_row["name"],
            })
            total_gel += subtotal
        else:
            # Include unpriced item with zero for transparency
            line_items.append({
                "name": comp["name"],
                "category": comp.get("category", ""),
                "quantity": comp.get("estimated_quantity", 1),
                "unit": comp.get("unit", "unit"),
                "unit_price_gel": None,
                "subtotal_gel": 0.0,
                "confidence": "low",
                "notes": "Price not found in database",
                "matched_item": None,
            })

    # Add typical labor estimate (30–40% of materials for Georgian market)
    labor_estimate = total_gel * 0.35
    total_with_labor = total_gel + labor_estimate

    estimate = {
        "session_id": session_id,
        "building_type": components_data.get("building_type", "unknown"),
        "construction_stage": components_data.get("construction_stage", "unknown"),
        "floor_area_m2": components_data.get("estimated_floor_area_m2"),
        "stories": components_data.get("estimated_stories", 1),
        "line_items": line_items,
        "materials_total_gel": round(total_gel, 2),
        "labor_estimate_gel": round(labor_estimate, 2),
        "grand_total_gel": round(total_with_labor, 2),
        "cost_per_m2_gel": round(total_with_labor / components_data["estimated_floor_area_m2"], 2)
            if components_data.get("estimated_floor_area_m2") else None,
        "confidence": components_data.get("overall_confidence", "medium"),
        "currency": "GEL",
        "notes": "Labor estimated at 35% of materials. Replace with actual quotes.",
        "analysis_notes": components_data.get("analysis_notes", ""),
    }

    approval_required = total_with_labor > LARGE_ESTIMATE_THRESHOLD

    return {
        **state,
        "cost_estimate": estimate,
        "current_step": "needs_review" if approval_required else "done",
        "approval_required": approval_required,
    }


def should_request_approval(state: AgentState) -> str:
    """LangGraph conditional edge function."""
    if state.get("approval_required") and not state.get("approval_granted"):
        return "needs_review"
    return "done"
