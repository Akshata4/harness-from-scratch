# End-to-end demo

A tiny real bug for the Stage 5 harness to autonomously find and fix,
end-to-end: run the failing test, diagnose it, patch the source, re-run to
confirm, report back — no hints given about where the bug is.

`toy_repo/calculator.py` has a genuine bug: `multiply(a, b)` returns `a + b`
instead of `a * b`. `toy_repo/test_calculator.py` has a test that catches
it (`test_multiply` expects `multiply(4, 5) == 20` but gets `9`). The source
file has no comment or hint pointing at the bug — the agent has to find it
from the test failure.

## 1. Confirm the bug is real

```bash
uv run pytest demo/toy_repo -q
```

Expect `1 failed, 3 passed`, with `assert 9 == 20` in the traceback.

## 2. Let the agent fix it

Run from the repo root, so the harness's workspace root covers `demo/`:

```bash
uv run python stage5_trajectory/main.py "There's a failing test in demo/toy_repo. Run its test suite with 'python -m pytest demo/toy_repo -q', figure out why the failing test fails, fix the bug in the source file (not the test file), then re-run the tests to confirm everything passes. Report what was wrong and what you changed."
```

You'll be asked to confirm two `run_bash` calls (the initial test run, and
the confirmation re-run after the fix).

Observed run (DeepSeek-V3 via OpenRouter, 4 turns): `run_bash` (pytest, sees
the failure) → `read_file` (calculator.py) → `write_file` (fixes `a + b` to
`a * b`, leaving every other line untouched) → `run_bash` (pytest again,
`4 passed`) → final report naming the exact bug and fix.

## 3. Verify independently

```bash
uv run pytest demo/toy_repo -q
```

Expect `4 passed`. Then reset the bug for the next run/demo take:

```bash
git checkout -- demo/toy_repo/calculator.py
```

## 4. Replay the run

The run from step 2 wrote a trajectory file — replay it to show the full
event-by-event record:

```bash
uv run python stage5_trajectory/main.py --replay trajectories/<the-file-from-step-2>.jsonl
```
