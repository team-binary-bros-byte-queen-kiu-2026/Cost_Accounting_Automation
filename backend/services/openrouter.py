"""
OpenRouter unified client.
Every call has: 30s timeout, exponential-backoff retry (max 3),
fallback model chain, prompt caching headers, and episode logging.
"""
import os
import time
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from . import episode_log

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
BASE_URL = "https://openrouter.ai/api/v1"
TIMEOUT = 30.0  # seconds

# Model fallback chain
PRIMARY_VISION_MODEL   = "google/gemini-2.0-flash"
SECONDARY_MODEL        = "anthropic/claude-3-5-haiku"
TERTIARY_MODEL         = "openai/gpt-4o-mini"

PRIMARY_CHAT_MODEL     = "anthropic/claude-3-5-haiku"

FALLBACK_CHAIN = [PRIMARY_VISION_MODEL, SECONDARY_MODEL, TERTIARY_MODEL]
CHAT_FALLBACK_CHAIN = [PRIMARY_CHAT_MODEL, SECONDARY_MODEL, TERTIARY_MODEL]

# Approximate cost per token (USD) — for logging
COST_MAP = {
    "google/gemini-2.0-flash":        {"input": 0.10 / 1_000_000, "output": 0.40 / 1_000_000},
    "anthropic/claude-3-5-haiku":     {"input": 0.80 / 1_000_000, "output": 4.00 / 1_000_000},
    "openai/gpt-4o-mini":             {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
}


def _calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = COST_MAP.get(model, {"input": 0.001 / 1000, "output": 0.002 / 1000})
    return input_tokens * rates["input"] + output_tokens * rates["output"]


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://construct-ai.kiu.edu.ge",
        "X-Title": "ConstructAI",
        "Content-Type": "application/json",
    }


def _is_retryable(exc: BaseException) -> bool:
    """Only retry on transient errors: timeouts and 5xx server errors."""
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return False


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=_is_retryable,
    reraise=True,
)
def _call_once(model: str, messages: list, **kwargs) -> dict:
    """Single attempt — tenacity retries on timeout or 5xx only."""
    payload = {"model": model, "messages": messages, **kwargs}
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.post(f"{BASE_URL}/chat/completions", headers=_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()


def chat(
    messages: list,
    session_id: str = "anonymous",
    model: str = PRIMARY_CHAT_MODEL,
    use_cache: bool = True,
    **kwargs,
) -> dict:
    """
    Chat call with fallback chain and episode logging.
    Returns: {content, model_used, input_tokens, output_tokens, fallback_triggered}
    """
    chain = CHAT_FALLBACK_CHAIN if model == PRIMARY_CHAT_MODEL else [model] + [m for m in FALLBACK_CHAIN if m != model]
    fallback_triggered = False
    last_error = None

    # Inject cache-control on system message if enabled
    if use_cache and messages and messages[0].get("role") == "system":
        messages = [
            {**messages[0], "cache_control": {"type": "ephemeral"}},
            *messages[1:],
        ]

    for idx, m in enumerate(chain):
        if idx > 0:
            fallback_triggered = True
        t0 = time.perf_counter()
        try:
            data = _call_once(m, messages, **kwargs)
            latency_ms = int((time.perf_counter() - t0) * 1000)

            usage = data.get("usage", {})
            input_tokens  = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            cache_read    = usage.get("cache_read_input_tokens", 0)
            cache_write   = usage.get("cache_creation_input_tokens", 0)
            cost          = _calc_cost(m, input_tokens, output_tokens)

            episode_log.log_llm_call(
                session_id=session_id,
                model=model,
                model_used=m,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
                cache_read_tokens=cache_read,
                cache_write_tokens=cache_write,
                fallback_triggered=fallback_triggered,
            )

            return {
                "content": data["choices"][0]["message"]["content"],
                "model_used": m,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_tokens": cache_read,
                "cache_write_tokens": cache_write,
                "fallback_triggered": fallback_triggered,
                "latency_ms": latency_ms,
                "cost_usd": cost,
            }
        except httpx.HTTPStatusError as e:
            last_error = e
            episode_log.log_llm_call(
                session_id=session_id,
                model=model,
                model_used=m,
                input_tokens=0,
                output_tokens=0,
                latency_ms=int((time.perf_counter() - t0) * 1000),
                cost_usd=0.0,
                fallback_triggered=fallback_triggered,
                error=str(e),
            )
            continue
        except Exception as e:
            last_error = e
            episode_log.log_llm_call(
                session_id=session_id,
                model=model,
                model_used=m,
                input_tokens=0,
                output_tokens=0,
                latency_ms=int((time.perf_counter() - t0) * 1000),
                cost_usd=0.0,
                fallback_triggered=fallback_triggered,
                error=str(e),
            )
            continue

    raise RuntimeError(f"All models in fallback chain failed. Last error: {last_error}")


def chat_with_fallback(
    messages: list,
    session_id: str = "anonymous",
    primary_model: str = PRIMARY_CHAT_MODEL,
    **kwargs,
) -> dict:
    """
    Lab 11 A2: explicit fallback catching RateLimitError and APIStatusError separately.
    """
    chain = [primary_model, SECONDARY_MODEL, TERTIARY_MODEL]
    fallback_triggered = False

    for idx, model in enumerate(chain):
        if idx > 0:
            fallback_triggered = True
        t0 = time.perf_counter()
        try:
            data = _call_once(model, messages, **kwargs)
            latency_ms = int((time.perf_counter() - t0) * 1000)
            usage = data.get("usage", {})
            input_tokens  = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            cost = _calc_cost(model, input_tokens, output_tokens)

            episode_log.log_llm_call(
                session_id=session_id,
                model=primary_model,
                model_used=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                cost_usd=cost,
                fallback_triggered=fallback_triggered,
            )
            return {
                "content": data["choices"][0]["message"]["content"],
                "model_used": model,
                "fallback_triggered": fallback_triggered,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": latency_ms,
                "cost_usd": cost,
            }

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # RateLimitError — try next model
                episode_log.log_llm_call(
                    session_id=session_id, model=primary_model, model_used=model,
                    input_tokens=0, output_tokens=0,
                    latency_ms=int((time.perf_counter() - t0) * 1000),
                    cost_usd=0.0, fallback_triggered=fallback_triggered, error="RateLimitError",
                )
                continue
            else:
                # APIStatusError — try next model
                episode_log.log_llm_call(
                    session_id=session_id, model=primary_model, model_used=model,
                    input_tokens=0, output_tokens=0,
                    latency_ms=int((time.perf_counter() - t0) * 1000),
                    cost_usd=0.0, fallback_triggered=fallback_triggered, error=f"APIStatusError:{e.response.status_code}",
                )
                continue
        except Exception as e:
            episode_log.log_llm_call(
                session_id=session_id, model=primary_model, model_used=model,
                input_tokens=0, output_tokens=0,
                latency_ms=int((time.perf_counter() - t0) * 1000),
                cost_usd=0.0, fallback_triggered=fallback_triggered, error=str(e),
            )
            continue

    raise RuntimeError("All models in fallback chain exhausted")


def vision_analyze(image_base64: str, prompt: str, session_id: str = "anonymous") -> dict:
    """Send an image to the vision model for analysis."""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
            ],
        }
    ]
    return chat(messages, session_id=session_id, model=PRIMARY_VISION_MODEL, use_cache=False)


def stream_chat(messages: list, session_id: str = "anonymous", model: str = PRIMARY_CHAT_MODEL):
    """
    Generator that yields SSE-formatted token chunks.
    Streams from OpenRouter, logs to episode_log on completion.
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    t0 = time.perf_counter()
    full_content = ""
    total_tokens = 0

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            with client.stream("POST", f"{BASE_URL}/chat/completions", headers=_headers(), json=payload) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk.strip() == "[DONE]":
                            yield "data: [DONE]\n\n"
                            break
                        try:
                            import json
                            data = json.loads(chunk)
                            delta = data["choices"][0]["delta"].get("content", "")
                            if delta:
                                full_content += delta
                                yield f"data: {json.dumps({'token': delta})}\n\n"
                        except Exception:
                            continue
    finally:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        # Approximate token count
        approx_tokens = len(full_content.split())
        episode_log.log_llm_call(
            session_id=session_id,
            model=model,
            model_used=model,
            input_tokens=sum(len(m.get("content", "").split()) for m in messages if isinstance(m.get("content"), str)),
            output_tokens=approx_tokens,
            latency_ms=latency_ms,
            cost_usd=_calc_cost(model, 500, approx_tokens),
        )
