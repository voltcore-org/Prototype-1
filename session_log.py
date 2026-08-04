"""
Prototype 1 - Session Log
Hybrid Algorithm Invention System (iOS LLM-Assist)

Plain-text/JSON session state. No database, no external services.
Call checkpoint() after every evaluated candidate -- that write is the
only state that survives app suspension or a thermal force-quit.
"""

import json
import os
import datetime

from problem_definition import PROBLEM_ID

DEFAULT_LOG_PATH = "prototype1_session_log.json"


def _now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def new_session(device: str, log_path: str = DEFAULT_LOG_PATH) -> dict:
    """Creates a fresh SessionLog dict in memory. Call checkpoint() to persist."""
    return {
        "problem_id": PROBLEM_ID,
        "device": device,
        "candidates": [],
        "results": [],
        "best_id": None,
        "human_notes": [],
        "checkpoint_path": log_path,
    }


def load_session(log_path: str = DEFAULT_LOG_PATH) -> dict:
    """Reopens a session log from disk, e.g. after a force-quit."""
    with open(log_path, "r") as f:
        return json.load(f)


def add_candidate(session: dict, candidate_id: str, source: str, origin: str) -> dict:
    """origin should be one of: 'claude', 'gpt', 'grok', 'human'."""
    entry = {
        "id": candidate_id,
        "source": source,
        "origin": origin,
        "timestamp": _now_iso(),
    }
    session["candidates"].append(entry)
    return entry


def add_result(session: dict, candidate_id: str, result: dict) -> dict:
    """result comes straight from evaluation_harness.evaluate_candidate()."""
    result = dict(result)
    result["candidate_id"] = candidate_id
    session["results"].append(result)

    current_best = session.get("best_id")
    if result["score"] < float("inf"):
        if current_best is None:
            session["best_id"] = candidate_id
        else:
            best_result = next(
                (r for r in session["results"] if r["candidate_id"] == current_best),
                None,
            )
            if best_result is None or result["score"] < best_result["score"]:
                session["best_id"] = candidate_id
    return result


def add_note(session: dict, note: str) -> None:
    session["human_notes"].append(f"{_now_iso()}  {note}")


def checkpoint(session: dict, log_path: str = None) -> str:
    """Writes the full session dict to disk. Call after every candidate."""
    path = log_path or session["checkpoint_path"]
    with open(path, "w") as f:
        json.dump(session, f, indent=2)
    return path


def write_highlight(session: dict, out_dir: str = ".") -> str:
    """Writes the human-readable highlight artifact. Pure string
    formatting -- no model call, no network access."""
    if session["results"]:
        best_id = session.get("best_id") or session["results"][-1]["candidate_id"]
        best_result = next(
            (r for r in session["results"] if r["candidate_id"] == best_id),
            session["results"][-1],
        )
        best_candidate = next(
            (c for c in session["candidates"] if c["id"] == best_result["candidate_id"]),
            {"source": "(candidate source not found)"},
        )
    else:
        best_result = {"score": None, "observation": "no results recorded", "runtime_ms": None}
        best_candidate = {"source": "(none)"}

    timestamp = _now_iso().replace(":", "-")
    filename = os.path.join(out_dir, f"prototype1_highlight_{timestamp}.txt")

    lines = [
        f"PROBLEM: {session['problem_id']}",
        f"DEVICE: {session['device']}",
        "",
        "BEST CANDIDATE SOURCE:",
        best_candidate["source"],
        "",
        f"SCORE (MSE): {best_result.get('score')}",
        f"OBSERVATION: {best_result.get('observation')}",
        f"RUNTIME_MS: {best_result.get('runtime_ms')}",
        "",
        "HUMAN NOTES:",
    ]
    lines.extend(session.get("human_notes") or ["(none recorded)"])
    lines.append("")
    lines.append(
        "STATUS: Prototype 1 result. No claim of foundational novelty. "
        "One human-gated propose-evaluate-filter cycle."
    )

    with open(filename, "w") as f:
        f.write("\n".join(lines))

    return filename


if __name__ == "__main__":
    s = new_session(device="iPhone15ProMax")
    add_candidate(s, "c1", "def candidate(x):\n    return 2*x**2 - 3*x + 1\n", "claude")
    add_result(s, "c1", {
        "score": 0.01, "passed": True, "observation": "self-test",
        "runtime_ms": 1.0, "memory_note": "n/a",
    })
    add_note(s, "self-test run")
    path = checkpoint(s)
    print("checkpointed to", path)
    reloaded = load_session(path)
    print("reloaded best_id:", reloaded["best_id"])
    hl = write_highlight(s)
    print("highlight written to", hl)
