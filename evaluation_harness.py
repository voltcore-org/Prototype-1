"""
Prototype 1 - Evaluation Harness
Hybrid Algorithm Invention System (iOS LLM-Assist)

Evaluates one pasted candidate against the fixed Prototype-1 dataset.

SCOPE / HONESTY NOTE (do not remove):
This is a constrained execution of a single function body, not a
general-purpose sandbox. It restricts the builtins available to the
candidate and exposes no file, network, or subprocess access from
inside this module -- but Python's dynamic nature means a determined
adversarial string could still misbehave. The actual security boundary
in this architecture is the human operator: read every candidate before
running it (workflow_notes.md, step 3). This module is a correctness
and convenience aid, not a sandbox, and must never be described as one.
"""

import math
import time
import traceback

from problem_definition import load_data, PROBLEM_ID

_SAFE_BUILTINS = {
    "abs": abs, "min": min, "max": max, "pow": pow, "round": round,
    "range": range, "len": len, "sum": sum, "float": float, "int": int,
    "True": True, "False": False, "None": None,
}

FAIL_SCORE = float("inf")
PASS_THRESHOLD = 0.05  # MSE below this counts as "passed" for this problem


def _build_namespace():
    ns = {"__builtins__": _SAFE_BUILTINS, "math": math}
    try:
        import numpy as np
        ns["np"] = np
    except ImportError:
        pass  # numpy not installed in this runtime -- candidate must not need it
    return ns


def _last_error_line() -> str:
    return traceback.format_exc(limit=1).strip().splitlines()[-1]


def evaluate_candidate(candidate_source: str) -> dict:
    """
    candidate_source: plain text defining exactly one function,
        def candidate(x): ...
    Returns an EvaluationResult dict:
        candidate_id, score, passed, observation, runtime_ms, memory_note
    candidate_id is filled in by the caller (session_log.add_result),
    not by this function.
    """
    X, y = load_data()
    start = time.perf_counter()
    namespace = _build_namespace()

    try:
        exec(candidate_source, namespace)
    except Exception:
        return {
            "candidate_id": None,
            "score": FAIL_SCORE,
            "passed": False,
            "observation": "candidate failed to compile/define: " + _last_error_line(),
            "runtime_ms": round((time.perf_counter() - start) * 1000, 3),
            "memory_note": "n/a (define-time failure)",
        }

    fn = namespace.get("candidate")
    if fn is None or not callable(fn):
        return {
            "candidate_id": None,
            "score": FAIL_SCORE,
            "passed": False,
            "observation": "candidate source did not define a callable named 'candidate(x)'",
            "runtime_ms": round((time.perf_counter() - start) * 1000, 3),
            "memory_note": "n/a",
        }

    squared_errors = []
    try:
        for xi, yi in zip(X, y):
            pred = fn(xi)
            squared_errors.append((float(pred) - yi) ** 2)
    except Exception:
        return {
            "candidate_id": None,
            "score": FAIL_SCORE,
            "passed": False,
            "observation": "candidate raised during evaluation: " + _last_error_line(),
            "runtime_ms": round((time.perf_counter() - start) * 1000, 3),
            "memory_note": "n/a (runtime failure)",
        }

    mse = sum(squared_errors) / len(squared_errors)
    runtime_ms = round((time.perf_counter() - start) * 1000, 3)

    return {
        "candidate_id": None,
        "score": round(mse, 6),
        "passed": mse < PASS_THRESHOLD,
        "observation": f"MSE={mse:.6f} over {len(X)} points on {PROBLEM_ID}",
        "runtime_ms": runtime_ms,
        "memory_note": "not measured on-device; watch the iOS memory-warning banner",
    }


def print_result(result: dict) -> None:
    print("-" * 40)
    print(f"candidate_id : {result.get('candidate_id')}")
    print(f"score (MSE)  : {result['score']}")
    print(f"passed       : {result['passed']}")
    print(f"observation  : {result['observation']}")
    print(f"runtime_ms   : {result['runtime_ms']}")
    print(f"memory_note  : {result['memory_note']}")
    print("-" * 40)


if __name__ == "__main__":
    # Self-test: one correct candidate, one deliberately broken candidate.
    good = "def candidate(x):\n    return 2*x**2 - 3*x + 1\n"
    bad = "def candidate(x):\n    return 1/0\n"

    print("== self-test: correct candidate ==")
    print_result(evaluate_candidate(good))

    print("== self-test: broken candidate ==")
    print_result(evaluate_candidate(bad))
