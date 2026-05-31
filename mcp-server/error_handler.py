"""
Error sanitization — callers never see tracebacks, file paths, or env vars.
Lab 8: caller only sees {"error": "tool_execution_failed"}.
"""


def safe_error(e: Exception) -> str:
    """Return a sanitized error message — no internal details exposed."""
    # Log full error internally (to stderr so MCP inspector can see it)
    import traceback, sys
    print(f"[MCP ERROR] {type(e).__name__}: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    # Return sanitized message to caller
    return "tool_execution_failed"
