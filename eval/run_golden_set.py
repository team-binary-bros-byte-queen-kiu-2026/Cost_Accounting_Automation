"""
Golden Set Evaluation Script — Cost Accounting Automation
CS-AI-2025 Lab 8, Spring 2026

Usage:
    export OPENROUTER_API_KEY=your_key
    export APP_ENDPOINT=http://localhost:8000/api/chat   # your running backend
    python eval/run_golden_set.py

Output:
    eval/results/golden-set-results-<timestamp>.json
    Terminal: pass/fail per question and overall score
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path

import httpx

# ─── Configuration ─────────────────────────────────────────────────────────

OR_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
JUDGE_MODEL = "google/gemini-2.5-flash-preview"
YOUR_APP_ENDPOINT = os.environ.get("APP_ENDPOINT", "http://localhost:8000/api/chat")
GOLDEN_SET_PATH = Path("eval/golden_set.json")
RESULTS_DIR = Path("eval/results")

# ─── Load Golden Set ───────────────────────────────────────────────────────

with open(GOLDEN_SET_PATH, encoding="utf-8") as f:
    GOLDEN_SET = json.load(f)

# ─── LLM Judge ─────────────────────────────────────────────────────────────

JUDGE_PROMPT = """You are an impartial evaluator assessing an AI assistant's response for a Georgian construction cost accounting application.

QUESTION ASKED:
{question}

EXPECTED ANSWER (guide only — exact wording not required):
{expected}

EVALUATION RUBRIC:
{rubric}

ACTUAL RESPONSE FROM AI ASSISTANT:
{actual}

Evaluate whether the actual response satisfies the rubric criteria. Output ONLY a valid JSON object:
{{"pass": true or false, "reason": "one sentence explaining your verdict", "score": 0.0 to 1.0}}

Do not output anything else. No markdown fences."""


async def judge_response(question: str, expected: str, rubric: str, actual: str) -> dict:
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OR_API_KEY}"},
            json={
                "model": JUDGE_MODEL,
                "messages": [{"role": "user", "content": JUDGE_PROMPT.format(
                    question=question, expected=expected,
                    rubric=rubric, actual=actual,
                )}],
                "max_tokens": 200,
                "temperature": 0.0,
            },
        )
        data = response.json()
        raw = data["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())


# ─── App Caller ────────────────────────────────────────────────────────────

async def call_your_app(question: str) -> str:
    """Call the cost accounting chatbot endpoint."""
    async with httpx.AsyncClient(timeout=35) as client:
        try:
            response = await client.post(
                YOUR_APP_ENDPOINT,
                json={"message": question, "conversation_history": []},
            )
            data = response.json()
            return data.get("content", data.get("response", data.get("message", str(data))))
        except Exception as e:
            return f"[APP_ERROR: {type(e).__name__}: {e}]"


# ─── Main Evaluation Loop ──────────────────────────────────────────────────

async def run_evaluation():
    if not OR_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set.")
        return

    print(f"Running golden set evaluation — {len(GOLDEN_SET)} questions")
    print(f"App endpoint : {YOUR_APP_ENDPOINT}")
    print(f"Judge model  : {JUDGE_MODEL}")
    print("-" * 60)

    results = []
    passing = 0
    start_time = time.time()

    for item in GOLDEN_SET:
        q_start = time.time()
        actual = await call_your_app(item["input"])

        try:
            verdict = await judge_response(
                question=item["input"],
                expected=item["expected"],
                rubric=item["rubric"],
                actual=actual,
            )
        except Exception as e:
            verdict = {"pass": False, "reason": f"Judge error: {e}", "score": 0.0}

        latency = round((time.time() - q_start) * 1000)
        if verdict["pass"]:
            passing += 1

        result = {
            **item,
            "actual_response": actual,
            "pass": verdict["pass"],
            "reason": verdict["reason"],
            "score": verdict.get("score", 1.0 if verdict["pass"] else 0.0),
            "latency_ms": latency,
        }
        results.append(result)

        status = "PASS" if verdict["pass"] else "FAIL"
        print(f"[{item['id']}] {status} — {item['category']} — {latency}ms")
        if not verdict["pass"]:
            print(f"       Reason: {verdict['reason']}")

    total_time = round(time.time() - start_time)
    print("-" * 60)
    print(f"Score: {passing}/{len(GOLDEN_SET)} ({round(passing / len(GOLDEN_SET) * 100)}%) in {total_time}s")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    results_path = RESULTS_DIR / f"golden-set-results-{timestamp}.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "score": f"{passing}/{len(GOLDEN_SET)}",
            "pass_rate": round(passing / len(GOLDEN_SET), 2),
            "total_time_seconds": total_time,
            "judge_model": JUDGE_MODEL,
            "results": results,
        }, f, indent=2)

    print(f"Results saved: {results_path}")
    return results


if __name__ == "__main__":
    asyncio.run(run_evaluation())
