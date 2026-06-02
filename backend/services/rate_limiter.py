"""
Per-IP sliding window rate limiter.
/analyze  → 20 requests/minute
/chat     → 60 requests/minute
Returns HTTP 429 with retry_after_seconds when exceeded.
"""
import time
from collections import defaultdict, deque
from fastapi import Request, HTTPException

# {ip: deque of timestamps}
_windows: dict[str, dict[str, deque]] = defaultdict(lambda: defaultdict(deque))

LIMITS = {
    "analyze": 20,   # per minute
    "chat":    60,
    "speak":   30,
    "transcribe": 20,
}
WINDOW_SECONDS = 60


def check_rate_limit(request: Request, endpoint: str):
    """Call this at the top of any rate-limited route."""
    ip = request.client.host or "unknown"
    limit = LIMITS.get(endpoint, 30)
    now = time.time()
    window = _windows[ip][endpoint]

    # Remove timestamps outside the window
    while window and window[0] < now - WINDOW_SECONDS:
        window.popleft()

    if len(window) >= limit:
        oldest = window[0]
        retry_after = int(WINDOW_SECONDS - (now - oldest)) + 1
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "retry_after_seconds": retry_after,
                "limit": limit,
                "window_seconds": WINDOW_SECONDS,
            },
        )

    window.append(now)
