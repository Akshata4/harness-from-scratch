# harness-from-scratch — Part A

A coding-agent harness built progressively, from a single LLM call to a full
tool-using agent loop with sandboxed execution and trajectory logging.

Every stage lives in its own folder and is independently runnable, so the
build-up can be demoed one stage at a time.

## LLM backend

The harness talks to the model through the OpenAI-compatible chat-completions
schema. Two providers are wired up behind one interface, selected by
`LLM_PROVIDER` in `.env`:

- **`openrouter`** (default) — [OpenRouter](https://openrouter.ai), `https://openrouter.ai/api/v1`
- **`wandb`** — [W&B Inference](https://docs.wandb.ai/inference/), `https://api.inference.wandb.ai/v1` (uses W&B credits)

Because both speak the same API shape, swapping providers is a one-line env
change — no code changes required. This is demonstrated in Stage 0.

## Setup

Dependencies are managed with [`uv`](https://docs.astral.sh/uv/) — no manual
venv/pip steps needed.

```bash
cp .env.example .env
# fill in OPENROUTER_API_KEY and/or WANDB_API_KEY + WANDB_PROJECT in .env
uv sync
```

Every stage is then run with `uv run`, e.g.:

```bash
uv run python stage0_single_call/main.py "Say hello and name the model you are"
```

## Stages

| Stage | Folder | Demonstrates |
|---|---|---|
| 0 | `stage0_single_call/` | Provider-agnostic client, one request/response |
| 1 | `stage1_chat_loop/` | Multi-turn conversation with history |
| 2 | `stage2_tools/` | Tool/function-calling schema, one tool round trip |
| 3 | `stage3_agent_loop/` | Full ReAct-style loop: call → tool → feed back → repeat until done |
| 4 | `stage4_shell_and_safety/` | Sandboxed `run_bash`, workspace confinement, confirmation gate |
| 5 | `stage5_trajectory/` | Append-only event log per run + replay |
| — | `demo/` | End-to-end: point the Stage 5 harness at a toy repo with a failing test and let it fix the bug autonomously |

Each stage folder has its own `README.md` explaining what changed and how to
run it.
