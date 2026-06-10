"""
Golden set evaluation script.
Calls the /chat/stream endpoint with a fixed session containing the price database,
then checks each answer against expected content.
Must complete in <3 minutes and achieve >=70% pass rate for CI to pass.
"""
import json
import sys
import os
import time
import uuid
import httpx
from pathlib import Path

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
GOLDEN_SET_PATH = Path(__file__).parent / "golden_set.json"
RESULTS_PATH = Path(__file__).parent / "results" / "latest.json"

# A pre-loaded session context summarizing the price database for evaluation
EVAL_CONTEXT = """You are ConstructAI, an expert construction cost estimator for the Georgian market.
Known prices: Concrete M300=185 GEL/m3, Ceramic tiles=28 GEL/m2, Mason=85 GEL/day,
Rebar 12mm=1.20 GEL/kg, PVC window=185 GEL/m2, AAC block=2.50 GEL/unit.
Answer questions about construction costs using these prices."""


def check_answer(answer: str, question: dict) -> bool:
    """Returns True if the answer passes the question's criteria."""
    # Normalise before matching:
    #   - remove thousands-separator commas so "3,330" matches "3330"
    #   - map unicode superscripts to ASCII so "m²" matches "m2", "m³" matches "m3"
    answer_normalised = (
        answer
        .replace(",", "")
        .replace("²", "2")
        .replace("³", "3")
    )
    answer_lower = answer_normalised.lower()

    # Check required terms
    for term in question.get("expected_contains", []):
        if term.lower() not in answer_lower:
            return False

    # Check that bad terms are absent
    for term in question.get("expected_not_contains", []):
        if term.lower() in answer_lower:
            return False

    # Check that at least one of these terms appears
    any_terms = question.get("expected_contains_any", [])
    if any_terms:
        if not any(t.lower() in answer_lower for t in any_terms):
            return False

    return True


def call_chat(session_id: str, message: str) -> str:
    """Call the chat stream endpoint and collect the full response."""
    full_text = ""
    try:
        with httpx.Client(timeout=60.0) as client:
            with client.stream(
                "POST",
                f"{BACKEND_URL}/chat/stream",
                json={"session_id": session_id, "message": message},
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk == "[DONE]":
                            break
                        try:
                            data = json.loads(chunk)
                            full_text += data.get("token", "")
                        except Exception:
                            pass
    except Exception as e:
        return f"ERROR: {e}"
    return full_text


def main():
    questions = json.loads(GOLDEN_SET_PATH.read_text())
    session_id = str(uuid.uuid4())

    # Prime the session with context
    print(f"Priming eval session {session_id}...")
    call_chat(session_id, f"System context: {EVAL_CONTEXT}")

    results = []
    passed = 0
    t_start = time.perf_counter()

    for q in questions:
        print(f"  [{q['id']}] {q['question'][:60]}...")
        t0 = time.perf_counter()
        answer = call_chat(session_id, q["question"])
        latency_ms = int((time.perf_counter() - t0) * 1000)
        ok = check_answer(answer, q)
        if ok:
            passed += 1
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"    {status} ({latency_ms}ms)")
        if not ok:
            print(f"    Answer: {answer[:200]}")

        results.append({
            "id": q["id"],
            "type": q["type"],
            "question": q["question"],
            "answer": answer,
            "passed": ok,
            "latency_ms": latency_ms,
        })

    total_time = round(time.perf_counter() - t_start, 1)
    pass_rate = passed / len(questions)

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total": len(questions),
        "passed": passed,
        "failed": len(questions) - passed,
        "pass_rate": round(pass_rate, 3),
        "total_time_seconds": total_time,
        "results": results,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Save timestamped copy (for Repository Review — 3+ run files required)
    timestamp = time.strftime("%Y-%m-%d-%H%M%S", time.gmtime())
    timestamped_path = RESULTS_PATH.parent / f"run-{timestamp}.json"
    timestamped_path.write_text(json.dumps(summary, indent=2))
    # Always overwrite latest.json (Safety Audit reads this)
    RESULTS_PATH.write_text(json.dumps(summary, indent=2))
    print(f"\n{'='*50}")
    print(f"Pass rate: {passed}/{len(questions)} = {pass_rate:.1%}")
    print(f"Total time: {total_time}s")
    print(f"Results saved: {timestamped_path} + {RESULTS_PATH}")

    # Exit non-zero if below threshold (blocks CI merge)
    if pass_rate < 0.70:
        print("❌ FAIL: pass rate below 0.70 threshold")
        sys.exit(1)
    else:
        print("✅ PASS: pass rate meets threshold")
        sys.exit(0)


if __name__ == "__main__":
    main()
