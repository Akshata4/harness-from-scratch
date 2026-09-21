# TODO scanner — a from-scratch DSH plugin

Registers an agent tool, `scan_todos`, that recursively scans the workspace
for `TODO:`/`FIXME:` comments and returns each one's file, line number, and
text.

This plugin was **not hand-written** — it was authored by prompting DSH's
own headless agent and letting it research the real Cordis/`dsh-tools` API
itself (via its own file-reading tools against reference material copied
into `../_reference/`), the way the assignment's "Creator Mode" workflow is
meant to work.

## Prompt 1 — initial authoring

```
Create a new DeepSeek Harness (Cordis) plugin for this project that registers an agent tool called scan_todos. The tool should recursively scan the workspace for lines containing TODO: or FIXME: and return each match's file path, line number, and text; render a friendly summary when there are hits, or 'No TODO/FIXME comments found.' when there are none.

Reference material for the exact plugin/tool API is in ./plugins/_reference/:
- dsh-tools-index.d.ts and dsh-tools-schema.d.ts define the ToolDefinition/defineTool types
- dsh-tool-fs-example.js is a full real plugin showing ctx.tools.register(defineTool({...})) in use (search it for 'applyReadTool' for one complete example)

Read those first to get the exact shapes right, then write the plugin to ./plugins/todo-scanner/src/index.ts. It should:
- export name and apply(ctx) following the minimal Cordis plugin pattern (a plugin is a function; the loader mounts it)
- use Node's built-in fs/path modules for the directory walk (no new dependencies), skipping node_modules, .git, .dsh-home, dist, and build directories
- scan starting from an optional path argument (default '.', resolved against process.cwd())

After writing the file, print its full final contents so I can review it.
```

This produced a genuinely solid first draft: correct `defineTool` shape,
JSON output schema, a `render` for the model-facing text, and — beyond what
was asked — `presentCall`/`presentResult` for a nicer UI card, matching
conventions it picked up from the reference file on its own.

### Two real bugs found while testing it

1. **Module resolution** — the generated file did a real runtime
   `import { defineTool } from "@deepseek-ai/dsh-tools"`, but a plugin
   loaded as a raw file path (`insert:` in `dsh.patch.yml`) has no
   `node_modules` chain connecting it to that package (it lives inside a
   profile-specific `.dsh-home/` directory the plugin file's location
   never walks up into). Fixed by giving `part-b-dsh/` its own
   `package.json` with `@deepseek-ai/dsh-tools`/`@deepseek-ai/cordis`
   installed at the exact versions the running harness uses.

2. **Invented constant** — the generated code called
   `ctx.systemPrompt.getSectionOrder("TOOL_SCAN_TODOS")`, a section-order
   constant that doesn't exist (it was pattern-matched from the reference
   file's real `"TOOL_READ"` constant, but invented for this new tool).
   Since `getSectionOrder` returned `undefined` for an unknown name, and
   `ctx.systemPrompt.section()` requires a finite number, this crashed
   DSH's own plugin boot — which also meant the agent couldn't fix it while
   the broken plugin was registered (chicken-and-egg: a crashing plugin
   prevents the harness that would fix it from starting at all). Fixed by
   temporarily removing the plugin from `dsh.patch.yml`, then re-prompting
   the now-bootable agent:

## Prompt 2 — fixing its own bug

```
The file ./plugins/todo-scanner/src/index.ts fails to load into DeepSeek Harness with this error:

TypeError: prompt section "tool:scan_todos" order must be a finite number
    at Proxy.section (@deepseek-ai/dsh-system-prompt/lib/index.js:239:46)

The problem is the call to ctx.systemPrompt.getSectionOrder("TOOL_SCAN_TODOS") in that file — that constant doesn't exist anywhere in the codebase (it was invented by pattern-matching the reference example's real TOOL_READ constant). Search the installed @deepseek-ai packages under .dsh-home/profiles/headless/node_modules/@deepseek-ai/ (especially dsh-system-prompt and dsh-tool-fs) to find out how a real plugin picks a valid, finite numeric order value for a NEW system-prompt section that has no existing named constant, then edit the file so it loads without error. Keep the rest of the plugin as-is. After fixing it, print the full final contents of the file.
```

The agent found the real neighboring order constants (`TOOL_GREP` = 1500,
`TOOL_JOBS` = 1600) and picked `1550` to sit logically between them — a
well-reasoned fix, not a guess.

## Demo

`demo/sample_calculator.py` has two planted comments: a `TODO:` and a
`FIXME:`. Run from `part-b-dsh/`:

```bash
export DSH_HOME=./.dsh-home
set -a && source ../.env && set +a
npx --yes @deepseek-ai/dsh --profile headless --patch ./dsh.patch.yml \
  "Use the scan_todos tool to scan the plugins/ directory for TODO/FIXME comments and tell me exactly what you find."
```

Verified result: it correctly found both planted comments
(`demo/sample_calculator.py:2` and `:7`) — plus, honestly, several
self-matches inside its own source (`todo-scanner/src/index.ts`), because
the plugin's own code and docstrings literally contain the strings
`TODO:`/`FIXME:`. That's not a bug — it's the same "a TODO scanner finds
itself" quirk any naive text-matching tool has, worth calling out in the
video rather than hiding.
