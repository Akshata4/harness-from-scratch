# Stage 3 — Full agent loop

Stage 2 handled exactly one tool round trip and then stopped, even if the
model wanted more. Stage 3 removes that cap and turns it into a real
ReAct-style loop:

```
call model (with tools) → tool_calls? → execute each → feed results back → call model again → ...
                        → no tool_calls? → print final answer, done
```

The loop terminates itself the moment the model responds with plain content
and no `tool_calls` — that's the model signaling it's done, no special
"finish" tool needed. `MAX_TURNS` (8) is a hard safety cap so a confused
model can't loop forever burning API calls.

A third tool, `write_file`, is added so the loop actually has something
worth chaining multiple tool calls for — e.g. "read this file, then write a
summary of it somewhere else" needs `read_file` then `write_file` in
sequence, which is exactly what Stage 2's single round trip couldn't do.

Still no sandboxing — `write_file` will create/overwrite anything the OS
user can write to. Stage 4 adds workspace confinement and a confirmation
gate (for `run_bash` specifically, since arbitrary shell execution is the
highest-risk tool).

## Run

```bash
uv run python stage3_agent_loop/main.py
```

The default prompt makes it read `stage0_single_call/README.md` and write a
summary to `stage3_agent_loop/demo_output/summary.md` — a two-tool,
two-turn task that Stage 2 could not have completed in one round trip.

Or give it your own multi-step task:

```bash
uv run python stage3_agent_loop/main.py "List the stage0, stage1, and stage2 directories, then write a comparison of them to stage3_agent_loop/demo_output/comparison.md"
```
