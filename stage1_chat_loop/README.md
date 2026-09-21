# Stage 1 — Multi-turn chat loop

Stage 0 sent one prompt and forgot it existed. LLMs are stateless — the
*only* reason a conversation feels continuous is that the harness resends
the entire transcript on every call. This stage adds that: a `messages`
list that starts with a system prompt and grows by two entries
(`user`, `assistant`) each turn, with the whole list resent every time.

Nothing else changed — `llm_client.py` is identical to Stage 0.

## Run

```bash
uv run python stage1_chat_loop/main.py
```

## Try, to see the memory work

```
you> my name is Ankur
assistant> ...
you> what's my name?
assistant> Ankur
```

Compare against Stage 0: running `stage0_single_call/main.py` twice in a row
has no memory of the first call, since each invocation sends only one
message with no history.
