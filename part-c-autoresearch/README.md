# Part C — a custom ML autoresearch harness

An autonomous research-scientist agent that iteratively improves a
classifier's validation accuracy, end to end: it edits a training script,
runs a real experiment, gets a deterministic keep-or-revert verdict, and
repeats — then writes its own final report. Built on the exact same
tool-calling agent loop from Part A, specialized with two new tools for
ML experimentation.

## Design, grounded in real prior art

Researching [`awesome-autoresearch`](https://github.com/WecoAI/awesome-autoresearch)
surfaced the actual minimal pattern real autoresearch harnesses use (AIDE
and similar): **propose** (agent edits a target file) → **execute** (run
it) → **evaluate** (did the metric improve?) → **iterate** (keep the
change or revert it). That's simpler than a hyperparameter-config
abstraction and reuses almost everything Part A already built.
[harnessengineering.vizuara.ai](https://harnessengineering.vizuara.ai/)
treats durability (checkpointing/replay) as a first-class harness
concern — which maps directly onto using **git commits as the keep/revert
mechanism**.

**Coding assistant**: this project's own Part A harness, routed through
**W&B Inference** (`deepseek-ai/DeepSeek-V3.1`) — reused rather than
hand-rolled again, and every reasoning step burns W&B credits by design.

## Structure

```
part-c-autoresearch/
├── llm_client.py     # W&B-first client (same pattern as Part A, different default)
├── tools.py           # read_file/write_file/list_dir (from Part A) + run_experiment + get_history
├── trajectory.py       # unchanged from Part A Stage 5
├── main.py              # the research loop
├── .workspace/            # gitignored — local scratch dir with its OWN git repo
│   ├── train.py            #   the file the agent iteratively edits
│   └── state.json           #   local log of every attempt: metric, kept/reverted
├── best_train.py            # committed — winning script from a verified run
└── REPORT.md                 # committed — the agent's own report from that run
```

`.workspace/` has its own nested git repo so the keep/revert churn (a dozen
small commits) never pollutes this project's real git history — only
`best_train.py`/`REPORT.md` get copied out as the committed deliverable
snapshot once a run finishes.

## Run it

```bash
set -a && source .env && set +a   # from the repo root, loads WANDB_API_KEY etc.
uv run python part-c-autoresearch/main.py
```

The task, tools, and a 12-experiment budget are all in the system prompt —
no arguments needed for the default run. `--replay <trajectory-file>`
reconstructs any past run from its log, same as Part A.

`.workspace/` is reset to the pristine baseline (plain `LogisticRegression`,
96.49% accuracy) and the W&B project cleared, ready for a fresh live run.

## Real debugging stories

Three genuine bugs were found and fixed while getting this to actually
work end to end — all better material for a video than a clean first try.

**1. `wandb.init()` silently reads an env var we already used for
something else.** `WANDB_PROJECT` was already our own convention (from
Part A/B) for an `"entity/project"` combo string — but the `wandb` SDK
*also* auto-reads an env var of that exact name as its own setting, and
does so during its own settings ingestion regardless of what's passed
explicitly as `project=`. The result: `wandb.init(project="part-c-autoresearch")`
still failed with `Invalid project name '<entity>/<project>': ... found '/'`
— the *env var's* value, not the argument. Fixed by overriding the env var
only for the duration of the `wandb.init()` call, then restoring it
immediately after — a permanent overwrite at import time broke
`llm_client.py`'s use of the same env var elsewhere in the same process
(traced precisely by checking the value before/after importing `tools`).

**2. A real, recurring model-output corruption bug.** DeepSeek-V3.1 (via
W&B Inference) periodically corrupted a handful of characters mid-generation
into a single stray `极` character, replacing fragments of variable names
(`y_train` → `y极`, `X_test_scaled` → `X_test_sc极`). This produced real
Python `SyntaxError`s/`NameError`s in the generated `train.py` — genuine,
reproducible backend behavior, not a bug in our harness. It happened at
least 5 times across one 12-experiment run.

**3. That corruption crashed the whole harness, twice, at two different
layers.** First, a corrupted tool call's JSON arguments failed
`json.loads()` in our own code — an uncaught exception that killed the
entire process mid-run, discarding 3 already-completed experiments. Fixed
by parsing defensively and, on failure, returning the model a tool result
telling it to retry with valid JSON instead of crashing. That surfaced a
*second*, subtler failure: even after handling the parse error locally, the
raw corrupted arguments were still stored in the conversation history and
resent to the API on the next turn — which the API itself then rejected
server-side with the same JSON error, crashing every subsequent turn.
Fixed by sanitizing the stored tool-call arguments (replacing an
unparseable string with `"{}"`) before it ever re-enters the conversation
history, so a single bad generation can never propagate forward.

## Verified result

A full real run (`trajectories/20260921-121351-132b79.jsonl`, replayable)
completed in 35 turns / 12 experiments, 0 crashes, exit code 0:

- **Baseline**: plain `LogisticRegression`, 96.49% accuracy
- **Best found**: `StandardScaler` + `LogisticRegression`, **98.25%** accuracy — a real, reproducible improvement (re-running `best_train.py` independently reproduces the exact same number)
- Tried and correctly rejected along the way: `RandomForestClassifier` (97.08%), `SVC` with an RBF kernel (97.66%), `AdaBoostClassifier` (97.08%), `MLPClassifier` (97.66%), a `VotingClassifier` ensemble (97.66%), cross-validated hyperparameter search (tied, not improved), and an `XGBoost` attempt that correctly failed since the package isn't installed
- 5 of the 12 attempts hit the model-corruption bug above and were correctly identified as failures and reverted, without derailing the run
- The agent's own `REPORT.md` conclusion: "Simplicity Wins — the simplest approach (scaled logistic regression) outperformed more complex models," correctly identifying feature scaling, not model complexity, as the real lever

Real, browsable W&B dashboard:
https://wandb.ai/akshata-madavi-san-jose-state-university/part-c-autoresearch
