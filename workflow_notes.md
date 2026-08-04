# Prototype 1 — Operator Workflow Notes
Hybrid Algorithm Invention System (iOS LLM-Assist)

Scope reminder: this is one human-gated propose -> evaluate -> filter
cycle on a fixed toy problem. No evolutionary loop, no closed-loop
automation, no on-device compilation, no claim of foundational novelty.
Runtime: Juno, Pyto, or Code App on iPhone 15 Pro Max (or 9th-gen iPad).

---

## 0. One-time setup (per device)

1. Install one supported local Python runtime (Juno, Pyto, or Code App).
2. Copy these three files into that runtime's working folder:
   - `problem_definition.py`
   - `evaluation_harness.py`
   - `session_log.py`
3. `numpy` is optional. The three files run on pure standard library;
   `evaluation_harness.py` will use numpy only if a candidate imports it
   as `np` and it happens to be installed in your runtime. If your
   runtime doesn't have numpy, just don't ask the LLM for numpy-based
   candidates -- plain Python `candidate(x)` functions are the default
   and are what the prompt template below asks for.
4. Optional self-test (recommended once per device, confirms nothing is
   broken before you spend a real cycle on it):
   ```
   python3 problem_definition.py
   python3 evaluation_harness.py
   python3 session_log.py
   ```
   Expected: dataset prints, a correct self-test candidate scores a low
   MSE and `passed: True`, a broken self-test candidate fails cleanly
   with `passed: False` and no crash, and `session_log.py` prints a
   `checkpointed to ...` line followed by `reloaded best_id: c1`.

---

## 1. Start a session (one line, run once per cycle)

```python
import session_log as sl
session = sl.new_session(device="iPhone15ProMax")   # or "iPad9"
```

---

## 2. Frame the problem in your cloud-LLM chat app

Open Claude, ChatGPT, or SuperGrok on the device and send this exact
framing prompt (copy `PROBLEM_DESCRIPTION` from `problem_definition.py`
if you've edited it -- otherwise this text matches the file as shipped):

> I'm running a small local evaluation harness. Approximate a hidden
> degree-2 polynomial. Domain is x in [-3, 3]. Output has a small
> amount of noise. A correct low-degree polynomial should reach
> mean-squared-error well under 0.05 across 20 fixed sample points.
> Write ONE Python function named `candidate(x)` that takes a single
> float `x` and returns a single float prediction. Use only plain
> Python (the `math` module is available if needed) -- no other
> imports, no file or network access, no class definitions, just the
> one function. Give me exactly one candidate. Keep it short.

If you want a second, different candidate, send a follow-up in the same
chat:

> Give me one more candidate, structurally different from your first
> one (e.g. different functional form), same constraints as before.

You now have one or two candidate blocks of Python text. Read each one
before doing anything else with it (this read is the actual security
boundary for this prototype -- see the note at the top of
`evaluation_harness.py`).

---

## 3. Evaluate each candidate

For candidate 1:

```python
from evaluation_harness import evaluate_candidate, print_result

candidate_1_source = """
def candidate(x):
    return 2*x**2 - 3*x + 1
"""   # <-- paste the LLM's exact text here, keep the def line intact

result_1 = evaluate_candidate(candidate_1_source)
print_result(result_1)

sl.add_candidate(session, "c1", candidate_1_source, origin="claude")
sl.add_result(session, "c1", result_1)
sl.checkpoint(session)   # <-- do this every time, not just at the end
```

Repeat for candidate 2 with id `"c2"` if you generated one.

If the runtime rejects the paste (syntax error, or evaluator reports a
compile-time failure): simplify the candidate by hand or discard it.
Never try to auto-repair it -- that is out of scope for Prototype 1.

---

## 4. Record a human note (optional but recommended)

```python
sl.add_note(session, "c1 had the right shape; c2 underfit badly")
sl.checkpoint(session)
```

---

## 5. Feed the best result back to the LLM (few-shot refinement)

Look at `session["best_id"]` to see which candidate is currently ahead,
then send this template back into the same chat:

> Here is your best candidate so far and its score:
>
> ```python
> <paste the winning candidate's source here>
> ```
> MSE: <paste the winning score here>
>
> Propose one revised candidate that should score lower (lower MSE is
> better) under the same constraints as before (plain Python only, one
> function named `candidate(x)`).

This closes one full propose -> evaluate -> filter cycle. You can stop
here, or manually repeat steps 3-5 with the new candidate -- Prototype 1
only requires one complete cycle to be considered proven.

---

## 6. End the session and write the highlight artifact

```python
highlight_path = sl.write_highlight(session)
print(highlight_path)
```

This writes `prototype1_highlight_<timestamp>.txt` into the runtime's
working folder. Open it, AirDrop it, or copy it out via the Files app.
If the write fails for any reason, the last `print_result(...)` output
already on screen is the recoverable highlight -- photograph or
transcribe it manually.

---

## 7. Interruption handling

- Thermal warning or low-memory warning at any point: stop immediately,
  do not start another evaluation, and run `sl.checkpoint(session)`
  right away with whatever is already recorded.
- App force-quit or backgrounded and killed: reopen the runtime and run
  `session = sl.load_session()` (or pass the exact checkpoint path if
  you changed it) to pick up exactly where you left off. `best_id` and
  every prior candidate/result survive this.

---

## 8. QC checklist (from the approved plan, section 11)

Items 1, 2, 3, 5, and 7 were run and verified in the build/test pass
that produced these files (see build note at the end of this
document). Items 4, 6, and 8 require the physical device and the
actual LLM conversation, so they are the operator's job to confirm
during the real on-device run:

1. [verified] Problem data loads without memory warning (pure Python
   list of 20 floats -- negligible footprint on any iOS runtime).
2. [verified] Harness evaluates a deliberately correct candidate and
   returns a near-zero MSE with `passed: True`.
3. [verified] Harness evaluates a deliberately broken candidate and
   returns a clear failure observation without crashing.
4. [operator to confirm on-device] Full cycle (chat -> paste -> evaluate
   -> log -> few-shot re-prompt) completes inside a single thermal
   window on the primary device.
5. [verified] SessionLog checkpoint survives a simulated force-quit
   (session was reloaded mid-cycle from disk and produced the correct
   `best_id` and full history).
6. [operator to confirm on-device] Peak memory / thermal-throttling
   events are noted; no run continues after sustained throttling.
7. [verified] Every intermediate candidate remains readable as plain
   text in the JSON session log -- no opaque binary state.
8. [operator to confirm at write time] Highlight file language stays
   inside the evidence posture (no foundational-novelty claims). The
   template in `session_log.write_highlight()` already includes a
   fixed disclaimer line for this.

Failure of any item blocks hand-off to Prototype 2, per the approved
plan.

---

## Build note (honesty / evidence posture)

`problem_definition.py`, `evaluation_harness.py`, and `session_log.py`
were written and executed end-to-end in a Linux sandbox during this
build pass, including: the module self-tests, and a full simulated
cycle (two candidates, a mid-cycle forced reload from disk, best-id
selection, and highlight-file generation). Output matched expectations
in every case shown above. What was NOT tested here: behavior on
actual iOS runtimes (Juno/Pyto/Code App), actual thermal/memory
pressure on a physical device, and the live LLM chat interaction --
those require the physical iPhone 15 Pro Max and are the operator's
step in section 0 and section 8 above. No result in this document is
claimed as verified beyond what was actually executed.
