"""
Prototype 1 - Problem Definition
Hybrid Algorithm Invention System (iOS LLM-Assist)

Fixed, reproducible problem instance for Prototype 1: symbolic regression
of a low-degree polynomial on a small fixed dataset (<= 30 points).

Do not edit the target function or SEED mid-session. Changing either
value creates a different problem instance and invalidates comparisons
against any earlier logged results.

Pure standard library. No numpy/scipy dependency for this file, so it
loads on any of the three supported runtimes (Juno, Pyto, Code App)
with zero setup.
"""

import random

PROBLEM_ID = "p1_polyreg_deg2_v1"

PROBLEM_DESCRIPTION = (
    "Approximate a hidden degree-2 polynomial. You will not be given the "
    "exact coefficients. You are given: the input domain is x in [-3, 3]; "
    "the output has a small amount of noise added; a correct low-degree "
    "polynomial should achieve mean-squared-error well under 0.05 across "
    "20 fixed sample points. Write ONE Python function named candidate(x) "
    "that takes a single float x and returns a single float prediction. "
    "Only plain Python and, if needed, the 'math' module are available "
    "inside the evaluator -- no imports of other libraries, no file or "
    "network access."
)

SEED = 20260804        # fixed seed -> identical dataset on every device
NUM_POINTS = 20         # <= 30 points, trivial memory footprint


def _true_function(x: float) -> float:
    """Hidden target. Not sent to the LLM -- only PROBLEM_DESCRIPTION is
    shared during framing (see workflow_notes.md, prompt template)."""
    return 2.0 * x**2 - 3.0 * x + 1.0


def load_data():
    """
    Returns (X, y) as plain Python lists of floats, length NUM_POINTS.
    Deterministic given SEED: identical output on iPhone, iPad, or
    anywhere else this file is run.
    """
    rng = random.Random(SEED)
    X = [round(rng.uniform(-3.0, 3.0), 4) for _ in range(NUM_POINTS)]
    noise = [round(rng.uniform(-0.15, 0.15), 4) for _ in range(NUM_POINTS)]
    y = [round(_true_function(x) + n, 4) for x, n in zip(X, noise)]
    return X, y


if __name__ == "__main__":
    X, y = load_data()
    print(PROBLEM_ID)
    print(PROBLEM_DESCRIPTION)
    print(f"\n{NUM_POINTS} points:")
    for xi, yi in zip(X, y):
        print(f"  x={xi:>8.4f}   y={yi:>8.4f}")
