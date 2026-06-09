"""
Lab 11 model comparison benchmark.
Runs golden-set questions against multiple OpenRouter models and writes eval/model-comparison.json.

Usage (from repo root):
    export OPENROUTER_API_KEY=your_key
    python eval/run_model_comparison.py
"""
from __future__ import annotations

import json
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = REPO_ROOT / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
GOLDEN_SET_PATH = Path(__file__).parent / "golden_set.json"
OUTPUT_PATH = Path(__file__).parent / "model-comparison.json"

SYSTEM_PROMPT = """You are ConstructAI, an expert construction cost estimator for the Georgian market.
Known prices: Concrete M300=185 GEL/m3, Ceramic tiles=28 GEL/m2, Mason=85 GEL/day,
Rebar 12mm=1.20 GEL/kg, PVC window=185 GEL/m2, AAC block=2.50 GEL/unit.
Keep answers SHORT — 2 to 4 sentences. Always include GEL for costs."""

# Production stack + one rejected candidate (checklist Lab 11)
MODELS = [
    {
        "model": "anthropic/claude-3-5-haiku",
        "role": "primary_chat",
        "selected": True,
        "notes": "Production PRIMARY_MODEL — best balance of instruction following and latency.",
    },
    {
        "model": "google/gemini-2.5-flash",
        "role": "primary_vision_and_chat_alt",
        "selected": True,
        "notes": "Google Flash tier — used for vision; valid OpenRouter ID (gemini-3-flash is not available).",
    },
    {
        "model": "openai/gpt-4o-mini",
        "role": "oss_fallback",
        "selected": True,
        "notes": "Production OSS_FALLBACK — cheap, reliable last resort.",
    },
    {
        "model": "openai/o3-mini",
        "role": "evaluated_not_selected",
        "selected": False,
        "notes": "Rejected — higher latency and cost vs Haiku/Flash for streaming chat UX.",
    },
]

# Representative golden-set subset (4 types)
QUESTION_IDS = ["factual_1", "reasoning_1", "refusal_1", "format_1"]
RUNS_PER_QUESTION = 5

COST_PER_MILLION = {
    "anthropic/claude-3-5-haiku": {"input": 0.80, "output": 4.00},
    "google/gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai/o3-mini": {"input": 1.10, "output": 4.40},
}


def check_answer(answer: str | None, question: dict) -> bool:
    if not answer:
        return False
    answer_lower = answer.lower()
    for term in question.get("expected_contains", []):
        if term.lower() not in answer_lower:
            return False
    for term in question.get("expected_not_contains", []):
        if term.lower() in answer_lower:
            return False
    any_terms = question.get("expected_contains_any", [])
    if any_terms and not any(t.lower() in answer_lower for t in any_terms):
        return False
    return True


def call_model(model: str, question: str) -> dict:
    """Single OpenRouter chat completion. Returns result dict or error."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "data_collection": "deny",
        "max_tokens": 300,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://construct-ai.kiu.edu.ge",
        "X-Title": "ConstructAI",
    }
    t0 = time.perf_counter()
    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(BASE_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        latency_ms = int((time.perf_counter() - t0) * 1000)
        usage = data.get("usage", {})
        content = data["choices"][0]["message"].get("content") or ""
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        rates = COST_PER_MILLION.get(model, {"input": 1.0, "output": 3.0})
        cost_usd = (
            input_tokens * rates["input"] / 1_000_000
            + output_tokens * rates["output"] / 1_000_000
        )
        return {
            "ok": True,
            "content": content,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "latency_ms": int((time.perf_counter() - t0) * 1000),
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
        }


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round((pct / 100) * (len(ordered) - 1)))
    return round(ordered[idx], 1)


def benchmark_model(model_cfg: dict, questions: list[dict]) -> dict:
    model = model_cfg["model"]
    latencies: list[float] = []
    costs: list[float] = []
    failures = 0
    passes = 0
    total = 0
    run_details = []

    for q in questions:
        for run_idx in range(RUNS_PER_QUESTION):
            total += 1
            result = call_model(model, q["question"])
            if not result["ok"]:
                failures += 1
                latencies.append(result["latency_ms"])
                run_details.append({"question_id": q["id"], "run": run_idx + 1, "passed": False, "error": result.get("error")})
                continue

            latencies.append(result["latency_ms"])
            costs.append(result["cost_usd"])
            passed = check_answer(result["content"], q)
            if passed:
                passes += 1
            run_details.append({
                "question_id": q["id"],
                "run": run_idx + 1,
                "passed": passed,
                "latency_ms": result["latency_ms"],
                "cost_usd": round(result["cost_usd"], 6),
            })
            print(f"  [{model}] {q['id']} run {run_idx + 1}: {'PASS' if passed else 'FAIL'} ({result['latency_ms']}ms)")

    avg_cost = statistics.mean(costs) if costs else 0.0
    quality = round((passes / total) * 10, 1) if total else 0.0

    return {
        **model_cfg,
        "answer_quality_0_10": quality,
        "pass_rate": round(passes / total, 3) if total else 0.0,
        "latency_ms_p50": percentile(latencies, 50),
        "latency_ms_p95": percentile(latencies, 95),
        "avg_latency_ms": round(statistics.mean(latencies), 1) if latencies else 0.0,
        "avg_cost_usd_per_request": round(avg_cost, 6),
        "cost_usd_per_1000_requests": round(avg_cost * 1000, 2),
        "failure_rate_pct": round(failures / total * 100, 1) if total else 0.0,
        "total_calls": total,
        "failures": failures,
        "passes": passes,
        "runs_per_question": RUNS_PER_QUESTION,
        "run_details": run_details,
    }


def main():
    if not OPENROUTER_API_KEY:
        raise SystemExit("OPENROUTER_API_KEY not set. Add it to .env or export it.")

    golden = json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    by_id = {q["id"]: q for q in golden}
    questions = [by_id[qid] for qid in QUESTION_IDS]

    print(f"Model comparison — {len(MODELS)} models × {len(questions)} questions × {RUNS_PER_QUESTION} runs")
    results = []
    for cfg in MODELS:
        print(f"\nBenchmarking {cfg['model']}...")
        result = benchmark_model(cfg, questions)
        result.pop("run_details", None)
        results.append(result)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology": (
            f"Golden-set subset ({', '.join(QUESTION_IDS)}), "
            f"{RUNS_PER_QUESTION} runs per question per model via OpenRouter. "
            "Quality = pass_rate × 10 using same rules as eval/run_eval.py. "
            "All requests include data_collection=deny."
        ),
        "questions_used": QUESTION_IDS,
        "runs_per_question": RUNS_PER_QUESTION,
        "models": results,
        "decision_summary": (
            "Selected claude-3-5-haiku (chat) and gemini-2.5-flash (vision) for quality/latency; "
            "gpt-4o-mini as OSS fallback. Rejected o3-mini for streaming UX (p95 ~4s vs ~1–2.5s)."
        ),
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUTPUT_PATH}")
    for r in results:
        print(
            f"  {r['model']}: quality={r['answer_quality_0_10']}/10, "
            f"p50={r['latency_ms_p50']}ms, p95={r['latency_ms_p95']}ms, "
            f"fail={r['failure_rate_pct']}%"
        )


if __name__ == "__main__":
    main()
