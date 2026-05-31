"""
Bearer token authentication — must be called BEFORE any tool logic.
Lab 8: bearer token verification executes before tool logic.
"""
import os

MCP_BEARER_TOKEN = os.environ.get("MCP_BEARER_TOKEN", "")


def verify_token(token: str | None) -> None:
    """Raise ValueError if token is invalid. Call this first in every tool."""
    if not MCP_BEARER_TOKEN:
        return  # Token auth disabled (dev mode without env var)
    if not token or token != MCP_BEARER_TOKEN:
        raise ValueError("Invalid or missing bearer token")
