# Part B — DeepSeek Harness (DSH) + plugins

[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (`dsh`) is
DeepSeek AI's open-source agent runtime: an "everything is a plugin"
architecture built on **Cordis**, where models, tools, sessions, sandboxing,
and the UI are all swappable plugins configured via YAML.

Installed via `npx` — no local clone or build needed:

```bash
npx --yes @deepseek-ai/dsh web
```

## Routing through W&B Inference

DSH defaults to DeepSeek's own hosted API. `dsh.patch.yml` in this folder is
a Cordis patch overlay that reroutes it through **W&B Inference** instead
(switched from OpenRouter after its account credit balance was exhausted),
reusing `WANDB_API_KEY` and `WANDB_PROJECT` from the shell environment (the
same values Part A's `.env` uses):

```bash
export DSH_HOME=./.dsh-home   # keep all DSH state inside this project, not ~/.dsh
set -a && source ../.env && set +a   # loads WANDB_API_KEY / WANDB_PROJECT
npx --yes @deepseek-ai/dsh --profile headless --patch ./dsh.patch.yml "your task here"
npx --yes @deepseek-ai/dsh web --patch ./dsh.patch.yml
```

`--profile headless` answers one task from the terminal and exits — no
browser needed, useful for scripted verification. `--profile web` boots the
full web UI (default `http://127.0.0.1:3080`), which is where Creator Mode
and the plugin demos happen.

W&B Inference is OpenAI-compatible but needs the team/project identified via
an `openai-project` request header (confirmed against liteLLM's provider
docs, since they have to document the wire format precisely) — set under
`headers` in the provider config, not as a special client kwarg, since DSH
talks to the raw HTTP API directly. Model id and available catalog were
confirmed live against `GET /v1/models` rather than guessed; `deepseek-ai/DeepSeek-V3.1`
was picked for strong tool-calling (an initial attempt with the smaller
`meta-llama/Llama-3.1-8B-Instruct` leaked raw tool-call syntax as text
instead of using the structured tool-calling channel — too weak a model for
this harness's agent loop).

### Debugging stories worth knowing about

Getting each provider working here surfaced genuine bug hunts, documented
because they're a good demonstration of reading an unfamiliar codebase's
source to find the real cause instead of guessing from docs:

**OpenRouter's 402 "requires more credits" on every request:**

1. Every request failed with OpenRouter's `402: requires more credits`,
   reporting a requested ceiling of ~139,000 tokens — far more than a
   one-sentence reply needs.
2. Tracing through the installed `@deepseek-ai/dsh-llm-pi-ai` and
   `@earendil-works/pi-ai` source showed the real mechanism: when DSH
   doesn't send an explicit `max_tokens`, OpenRouter's own credit preflight
   reserves the model's *entire* context window as a worst case — a
   well-documented OpenRouter quirk, not a DSH-specific bug.
3. Capping `maxTokens`/`contextWindow` on the model entry in `dsh.patch.yml`
   is the fix — but it silently had **no effect** at first, across many
   config variations (different field names, different route names, etc.),
   with byte-for-byte identical error output every time.
4. The actual cause: DSH's session/model-info resolution caches the
   *first* resolved value for a given `$DSH_HOME`, and later config edits
   don't back-fill into that cache. A completely fresh `$DSH_HOME` picked
   up the corrected config immediately and worked first try.

**Switching to W&B, the old provider kept getting used anyway:**

After swapping the patch file's provider from `openrouter` to `wandb`, DSH
failed with `NO_ADAPTER: no adapter registered for provider "openrouter"` —
it was still trying to use the *deleted* provider. Cause: `agent-default-model`
reads a **live** settings store (`$DSH_HOME/settings.yaml`), which gets
auto-written with the user's actual selection during normal use and takes
priority over the static `cordis.patch.yml`/`--patch` composition. Fixing
`agent-default-model:` in that file directly (not just the patch overlay)
resolved it. Lesson: a provider/model switch needs updating in *two* places
— the patch file (the intended default) and `$DSH_HOME/settings.yaml` (the
live override) — or a fresh `$DSH_HOME`.

## Marketplace plugins (7, installed on the `web` profile)

Picked from the real [`awesome-dsh-plugin`](https://github.com/awesome-dsh-plugin/awesome-dsh-plugin)
catalog for diverse capabilities and no external-service setup:

| Package | What it does |
|---|---|
| `dsh-about-plugin` | About/version panel in Web Settings |
| `dsh-taskboard` | Session-based task board with drag columns |
| `@0xsline/dsh-spotlight` | Keyboard-first command palette |
| `@anionex/dsh-turn-rewind` | Turn-level conversation/workspace rewind via a change ledger |
| `dsh-code-collector` | Gathers every code block from the current session |
| `dsh-answer-reviewer` | A separate LLM grades each final turn 1–100, steering the agent on low scores |
| `dsh-live2d-pet` | A visible companion in the UI — an unambiguous "yes it's installed" signal |

Install (per profile — these are UI plugins, so they need to be on `web`,
not `headless`):

```bash
export DSH_HOME=./.dsh-home
npx --yes @deepseek-ai/dsh plugin --profile web add dsh-about-plugin
npx --yes @deepseek-ai/dsh plugin --profile web add dsh-taskboard
npx --yes @deepseek-ai/dsh plugin --profile web add @0xsline/dsh-spotlight
npx --yes @deepseek-ai/dsh plugin --profile web add @anionex/dsh-turn-rewind
npx --yes @deepseek-ai/dsh plugin --profile web add dsh-code-collector
npx --yes @deepseek-ai/dsh plugin --profile web add dsh-answer-reviewer
npx --yes @deepseek-ai/dsh plugin --profile web add dsh-live2d-pet
```

### Second bug: a plugin with a missing peer dependency crashed the whole server

`@0xsline/dsh-spotlight` imports `schemastery` (DSH's validation library)
without declaring it as a real dependency, so `pnpm` never installed it. The
result wasn't a disabled plugin — it was a **hard crash of the entire web
profile** at boot (`ERR_MODULE_NOT_FOUND`), taking down all 7 plugins with
it. One broken third-party plugin is a single point of failure for the
whole harness. Fixed (at the time) by installing the missing package
directly: `npx --yes @deepseek-ai/dsh plugin --profile web add schemastery`.

### Third issue: the chat input stopped accepting keystrokes entirely

Later, in a normal browser session, the composer stopped accepting any
typed input. `@0xsline/dsh-spotlight` — a *global* keyboard-command-palette
plugin — was the leading suspect for swallowing keystrokes app-wide, so it
was uninstalled (`dsh plugin --profile web remove @0xsline/dsh-spotlight`)
as a diagnostic alongside a full server restart and a fresh browser
session. Input worked again afterward — but since the restart and fresh
session happened at the same time as the removal, root cause is not fully
isolated; it's plausibly a stale WebSocket connection from the restart
rather than the plugin itself. Left uninstalled since 6 plugins still
satisfies the assignment's 5–7 range and it wasn't reinstalled to re-test
in isolation.

**Current marketplace plugins (6, active):** `dsh-about-plugin`,
`dsh-taskboard`, `@anionex/dsh-turn-rewind`, `dsh-code-collector`,
`dsh-answer-reviewer`, `dsh-live2d-pet`.

## From-scratch plugins (2)

Both in `plugins/`, both authored by prompting DSH's own agent rather than
hand-written (genuine "Creator Mode" plugin authorship) — each required a
follow-up round of the agent debugging its own generated code before it
actually worked. Full prompts, bugs, and fixes documented in each one's
own README:

- **[`plugins/todo-scanner/`](plugins/todo-scanner/README.md)** — a
  `scan_todos` tool that recursively finds `TODO:`/`FIXME:` comments
- **[`plugins/break-reminder/`](plugins/break-reminder/README.md)** — a
  repeating timer that logs a break reminder every N minutes

`plugins/_reference/` holds the real DSH source files (tool/timer plugin
type definitions and a full working example) that were copied into the
project so the agent could read them from within its own sandboxed
workspace — the packages themselves live in `npx`'s global cache, outside
the harness's file-tool sandbox.

`part-b-dsh/package.json` exists solely so these plugin files (loaded as
raw TypeScript via `insert:` in `dsh.patch.yml`, not as installed npm
packages) can resolve `@deepseek-ai/dsh-tools`/`@deepseek-ai/cordis` at
runtime — a plugin loaded by file path has no `node_modules` chain to the
profile-specific packages inside `.dsh-home/`.
