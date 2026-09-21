# Stage 2 — Tool calling (single round trip)

Introduces the OpenAI function/tool-calling schema. Two tools are defined in
`tools.py` — `read_file` and `list_dir` — described as JSON schemas the model
can choose to invoke. Nothing forces a tool call; the model decides based on
the prompt whether it needs real information instead of guessing.

This stage runs the mechanism exactly once, deliberately *not* looped, so
the moving parts are visible in isolation before Stage 3 generalizes it into
a repeating agent loop:

1. Send the prompt plus the tool schemas.
2. If the model responds with `tool_calls`, execute each one locally and
   append its result back into the conversation as a `role: "tool"` message
   (matched to the call by `tool_call_id`).
3. Send one follow-up request so the model can produce a final
   natural-language answer, grounded in the real tool output.

There is no sandboxing yet — `read_file`/`list_dir` can read anything the OS
user running the script can read. Stage 4 adds a workspace confinement
boundary; this stage is intentionally "before that" to keep the tool-calling
mechanism itself the only new concept.

## Run

```bash
uv run python stage2_tools/main.py "What files are in the stage0_single_call directory, and what does main.py do?"
```

Try a prompt that needs no tool at all (e.g. `"What is 2+2?"`) to see the
model skip tool calling entirely and answer directly.
