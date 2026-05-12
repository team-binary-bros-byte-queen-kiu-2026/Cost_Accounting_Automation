"""
LLM Client — Cost Accounting Automation
CS-AI-2025, Spring 2026

Wraps all OpenRouter / OpenAI calls with:
  - asyncio timeout (30 s default)
  - Exponential backoff retry (3 attempts, 1 s / 2 s / 4 s)
  - Episode log entry on every call (success and failure)
  - Fallback chain: primary → fallback model on 5xx / timeout
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────

OR_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OR_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

PRIMARY_CHAT_MODEL = "openai/gpt-4.1"
FALLBACK_CHAT_MODEL = "openai/gpt-4o-mini"

PRIMARY_PARSE_MODEL = "openai/gpt-4o"
FALLBACK_PARSE_MODEL = "openai/gpt-4o-mini"

EPISODE_LOG_PATH = Path(os.environ.get("EPISODE_LOG_PATH", "logs/episode-log.jsonl"))

LLM_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
BACKOFF_BASE = 1.0  # seconds; doubled each retry


# ─── Episode Logger ────────────────────────────────────────────────────────

def _log_llm_call(
    model: str,
    provider: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
    cache_write_tokens: int,
    cost_usd: float,
    latency_ms: int,
    fallback_triggered: bool,
    error: Optional[str] = None,
) -> None:
    EPISODE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": round(time.time(), 3),
        "event_type": "llm_call",
        "model": model,
        "provider": provider,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": cache_write_tokens,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "fallback_triggered": fallback_triggered,
        "error": error,
    }
    with open(EPISODE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _estimate_cost(model: str, input_tokens: int, output_tokens: int,
                   cache_read_tokens: int) -> float:
    """Rough cost estimate based on OpenAI published pricing (per 1M tokens)."""
    pricing = {
        "openai/gpt-4.1":        (2.00, 8.00, 0.50),   # in, out, cache_read per 1M
        "openai/gpt-4o":         (2.50, 10.00, 1.25),
        "openai/gpt-4o-mini":    (0.15, 0.60, 0.075),
    }
    in_p, out_p, cache_p = pricing.get(model, (1.00, 4.00, 0.25))
    return round(
        (input_tokens / 1_000_000) * in_p
        + (output_tokens / 1_000_000) * out_p
        + (cache_read_tokens / 1_000_000) * cache_p,
        8,
    )


# ─── Core Call ────────────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    fallback_triggered: bool = False


async def _call_once(
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    timeout: float,
) -> dict:
    """Single HTTP call to OpenRouter with timeout."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            OR_BASE_URL,
            headers={
                "Authorization": f"Bearer {OR_API_KEY}",
                "HTTP-Referer": "https://github.com/team-binary-bros-byte-queen-kiu-2026",
                "X-Title": "Cost Accounting Automation",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def call_llm(
    messages: list[dict],
    model: str = PRIMARY_CHAT_MODEL,
    fallback_model: str = FALLBACK_CHAT_MODEL,
    temperature: float = 0.2,
    max_tokens: int = 1024,
    timeout: float = LLM_TIMEOUT_SECONDS,
) -> LLMResponse:
    """
    Call the LLM with timeout, retry, exponential backoff, and fallback.
    Logs every attempt (success or failure) to the episode log.
    """
    start = time.time()
    last_error: Optional[str] = None
    fallback_triggered = False

    for attempt in range(MAX_RETRIES):
        current_model = model
        try:
            data = await asyncio.wait_for(
                _call_once(current_model, messages, temperature, max_tokens, timeout),
                timeout=timeout,
            )
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            cache_read = usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
            cache_write = 0
            latency_ms = round((time.time() - start) * 1000)
            cost = _estimate_cost(current_model, input_tokens, output_tokens, cache_read)

            _log_llm_call(
                model=current_model,
                provider="openai",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read,
                cache_write_tokens=cache_write,
                cost_usd=cost,
                latency_ms=latency_ms,
                fallback_triggered=fallback_triggered,
                error=None,
            )

            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=current_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read,
                cache_write_tokens=cache_write,
                cost_usd=cost,
                latency_ms=latency_ms,
                fallback_triggered=fallback_triggered,
            )

        except (asyncio.TimeoutError, httpx.HTTPStatusError, httpx.RequestError) as e:
            last_error = type(e).__name__
            latency_ms = round((time.time() - start) * 1000)
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed ({last_error})")

            # On last retry with primary model, switch to fallback
            if attempt == MAX_RETRIES - 2 and current_model == model and fallback_model:
                logger.info(f"Switching to fallback model: {fallback_model}")
                model = fallback_model
                fallback_triggered = True

            if attempt < MAX_RETRIES - 1:
                backoff = BACKOFF_BASE * (2 ** attempt)
                logger.info(f"Waiting {backoff}s before retry...")
                await asyncio.sleep(backoff)
            else:
                _log_llm_call(
                    model=current_model,
                    provider="openai",
                    input_tokens=0,
                    output_tokens=0,
                    cache_read_tokens=0,
                    cache_write_tokens=0,
                    cost_usd=0.0,
                    latency_ms=latency_ms,
                    fallback_triggered=fallback_triggered,
                    error=last_error,
                )
                raise RuntimeError(f"All {MAX_RETRIES} attempts failed. Last error: {last_error}")
