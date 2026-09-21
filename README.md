# harness-from-scratch

Three-part project on building and extending AI coding-agent harnesses:
a from-scratch harness, a deep dive into an existing plugin-based harness
(DeepSeek Harness), and a custom ML autoresearch harness built on top of
Part A's own work.

| Part | What it is | Video | Details |
|---|---|---|---|
| A | A coding-agent harness built progressively from a single LLM call to a full tool-using agent loop with sandboxing and trajectory logging | [demo](https://youtu.be/GGK-tBdYchU) | below |
| B | DeepSeek Harness (DSH) installed, routed through W&B Inference, extended with 6 marketplace plugins and 2 plugins authored by prompting DSH's own agent | [demo](https://youtu.be/PFH9yRJJxeg) | [`part-b-dsh/README.md`](part-b-dsh/README.md) |
| C | A custom ML autoresearch harness, built on Part A's own agent, that autonomously improves a classifier's accuracy end to end and reports its findings | [demo](https://youtu.be/VWeCEH-ycGY) | [`part-c-autoresearch/README.md`](part-c-autoresearch/README.md) |

---

## Part A — coding harness from scratch

A coding-agent harness built progressively, from a single LLM call to a full
tool-using agent loop with sandboxed execution and trajectory logging.

Every stage lives in its own folder and is independently runnable, so the
build-up can be demoed one stage at a time.

### LLM backend

The harness talks to the model through the OpenAI-compatible chat-completions
schema. Two providers are wired up behind one interface, selected by
`LLM_PROVIDER` in `.env`:

- **`openrouter`** (default) — [OpenRouter](https://openrouter.ai), `https://openrouter.ai/api/v1`
- **`wandb`** — [W&B Inference](https://docs.wandb.ai/inference/), `https://api.inference.wandb.ai/v1` (uses W&B credits)

Because both speak the same API shape, swapping providers is a one-line env
change — no code changes required. This is demonstrated in Stage 0.

### Setup

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

### Stages

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

## Part B — DeepSeek Harness (DSH) + plugins

[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) is
DeepSeek AI's open-source "everything is a plugin" agent runtime. This part
installs it, routes it through W&B Inference, installs 6 real plugins from
the community marketplace, and builds two more from scratch — not by hand,
but by prompting DSH's own agent to author them, including it debugging its
own generated bugs across several rounds.

Full setup, the real debugging stories (a credit-preflight quirk, a
missing-dependency crash, a shell-quoting bug, and more), and both
from-scratch plugins' exact authoring prompts are in
[`part-b-dsh/README.md`](part-b-dsh/README.md).

## Part C — custom ML autoresearch harness

An autonomous research-scientist agent, built by extending Part A's own
harness rather than starting over: it edits a training script, runs a real
experiment, gets a deterministic keep-or-revert verdict (git commit or
git checkout, never the LLM's own call), repeats across a fixed budget, and
writes its own final report.

Verified end to end: a baseline classifier at 96.49% accuracy improved
autonomously to 98.25%+ on the scikit-learn breast-cancer dataset, with
every experiment logged to a real W&B project dashboard. Full design
rationale (grounded in real autoresearch harnesses researched on GitHub),
three real bugs found and fixed, and the verified results are in
[`part-c-autoresearch/README.md`](part-c-autoresearch/README.md).
