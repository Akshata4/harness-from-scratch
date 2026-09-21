# Stage 5 — Trajectory logging and replay

Every run so far has printed its progress to the terminal and then thrown
that record away the moment the process exits. This stage adds
`trajectory.py`: an append-only JSONL event log, one file per run, written
to `trajectories/<timestamp>-<id>.jsonl` (gitignored — these are run
artifacts, not source).

Four event types are logged, each the moment it happens (flushed to disk
immediately, not buffered until the end — so a crash mid-run still leaves a
usable partial log):

- `meta` — provider/model for the run
- `system` / `user` — the initial prompt pair
- `assistant` — each model turn: its text content and/or the tool calls it requested
- `tool` — each tool's name, arguments, and result

## Replay

```bash
uv run python stage5_trajectory/main.py --replay trajectories/<file>.jsonl
```

`replay_file()` reprints the log in the exact same format the live run used
— tool calls, results, final answer — which proves the log is a complete,
faithful record of what happened, not just a summary. This is the same idea
behind the "trajectory" / event-stream concept used for inspecting and
resuming agent runs in more advanced harnesses (Part B's DSH creator mode
leans on exactly this).

## Run

```bash
uv run python stage5_trajectory/main.py
```

Note the printed `[trajectory] logging this run to trajectories/...jsonl`
line — copy that path into the `--replay` command above afterwards.
