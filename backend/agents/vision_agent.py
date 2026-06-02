"""
Vision specialist agent.
Takes an image → returns identified building components with quantities.
"""
import json
from .state import AgentState
from ..services import openrouter

VISION_SYSTEM_PROMPT = """You are a construction cost estimation assistant specializing in analyzing building project photos.
When given a photo of a construction project or building, identify all visible construction components.

Return ONLY a valid JSON object with this structure:
{
  "building_type": "residential/commercial/industrial",
  "construction_stage": "foundation/structure/finishing/complete",
  "estimated_floor_area_m2": <number or null>,
  "estimated_stories": <number>,
  "components": [
    {
      "name": "<component name matching price database>",
      "category": "<concrete/masonry/steel/roofing/insulation/finishes/openings>",
      "estimated_quantity": <number>,
      "unit": "<m3/m2/kg/unit/lin_m>",
      "confidence": "<high/medium/low>",
      "notes": "<any relevant observation>"
    }
  ],
  "overall_confidence": "<high/medium/low>",
  "analysis_notes": "<general observations about the project>"
}

Be conservative with quantities when not clearly visible. Use "low" confidence for anything estimated.
"""


def vision_node(state: AgentState) -> AgentState:
    """LangGraph node: analyze image and identify components."""
    image_base64 = state.get("image_base64")
    if not image_base64:
        return {**state, "error": "No image provided", "current_step": "done"}

    result = openrouter.vision_analyze(
        image_base64=image_base64,
        prompt=VISION_SYSTEM_PROMPT,
        session_id=state["session_id"],
    )

    content = result["content"]
    # Extract JSON from the response
    try:
        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        components = json.loads(content)
    except json.JSONDecodeError:
        components = {
            "building_type": "unknown",
            "construction_stage": "unknown",
            "estimated_floor_area_m2": None,
            "estimated_stories": 1,
            "components": [],
            "overall_confidence": "low",
            "analysis_notes": content,
        }

    return {
        **state,
        "identified_components": components,
        "current_step": "estimation",
        "model_used": result["model_used"],
        "fallback_triggered": result["fallback_triggered"],
        "cache_read_tokens": result.get("cache_read_tokens", 0),
        "cache_write_tokens": result.get("cache_write_tokens", 0),
        "latency_ms": result.get("latency_ms", 0),
    }
