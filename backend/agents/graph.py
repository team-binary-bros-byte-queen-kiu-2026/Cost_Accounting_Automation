"""
LangGraph orchestration graph.
vision_node → estimation_node → [conditional] → done | needs_review
Lab 7 requirement: 2-node graph with conditional routing.
"""
from langgraph.graph import StateGraph, END
from .state import AgentState
from .vision_agent import vision_node
from .estimation_agent import estimation_node, should_request_approval


def human_review_node(state: AgentState) -> AgentState:
    """
    Placeholder for human-in-the-loop review.
    Large estimates (>500,000 GEL) land here.
    In production: send notification and wait for approval.
    For demo: auto-approve with a warning note.
    """
    estimate = state.get("cost_estimate", {})
    if estimate:
        estimate["notes"] = (
            "⚠️  REVIEW REQUIRED: This estimate exceeds 500,000 GEL. "
            "Please verify all quantities and get professional quotes before proceeding. "
            + estimate.get("notes", "")
        )
    return {**state, "cost_estimate": estimate, "approval_granted": True, "current_step": "done"}


def create_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("vision", vision_node)
    workflow.add_node("estimation", estimation_node)
    workflow.add_node("human_review", human_review_node)

    # Set entry point
    workflow.set_entry_point("vision")

    # Edges
    workflow.add_edge("vision", "estimation")
    workflow.add_conditional_edges(
        "estimation",
        should_request_approval,
        {
            "done": END,
            "needs_review": "human_review",
        },
    )
    workflow.add_edge("human_review", END)

    return workflow.compile()


# Module-level compiled graph (instantiated once)
estimation_graph = create_graph()


def run_estimation(session_id: str, image_base64: str) -> dict:
    """Run the full vision → estimation pipeline and return the cost estimate."""
    initial_state: AgentState = {
        "session_id": session_id,
        "user_request": "Analyze this building and estimate construction cost",
        "image_path": None,
        "image_base64": image_base64,
        "message_history": [],
        "current_step": "vision",
        "approval_required": False,
        "approval_granted": False,
        "retry_count": 0,
        "timeout_ms": 30000,
        "identified_components": None,
        "cost_estimate": None,
        "model_used": "",
        "fallback_triggered": False,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "latency_ms": 0,
        "error": None,
    }
    final_state = estimation_graph.invoke(initial_state)
    return final_state
