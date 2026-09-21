# Stage 0 — Single call

The smallest possible thing: one request, one response, no history, no tools.

The point of this stage is `llm_client.py` — a single function that returns
an `OpenAI` client configured for whichever provider `.env` points at. Both
OpenRouter and W&B Inference implement the OpenAI chat-completions schema, so
`main.py` never has to know which one it's talking to.

## Run

```bash
uv run python stage0_single_call/main.py "Say hello and name the model you are"
```

Try switching `LLM_PROVIDER` between `openrouter` and `wandb` in the root
`.env` and re-running — same code, different backend, different model
answering.
