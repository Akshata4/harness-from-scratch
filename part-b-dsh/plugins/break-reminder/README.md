# Break-reminder heartbeat — a from-scratch DSH plugin

A repeating timer that logs a friendly break reminder to the console every
N minutes while the harness is running (default 20, configurable).

Like the TODO scanner, this was authored by prompting DSH's own headless
agent rather than hand-written — and it took *two* rounds of the agent
debugging its own boot-time bugs before it worked, which is arguably the
more honest and interesting demo of "Creator Mode" than a clean one-shot
success would have been.

## Prompt 1 — initial authoring

```
Create a new DeepSeek Harness (Cordis) plugin for this project called break-reminder. It should use a repeating timer to log a friendly break-reminder message to the console every N minutes while the harness is running (default 20 minutes, configurable via a plugin config option intervalMinutes).

Reference material is in ./plugins/_reference/cordis-plugin-timer.ts — it's the real timer service's source, showing the ctx.interval(callback, delayMs) API and how timers are auto-disposed with the plugin. Read it first.

Write the plugin to ./plugins/break-reminder/src/index.ts. It should:
- export name and apply(ctx, config) following the minimal Cordis plugin pattern
- accept an optional config object with intervalMinutes (default 20)
- use ctx.interval(...) for the repeating timer (not a raw setInterval), so it's cleaned up automatically if the plugin unloads
- log a clear, friendly reminder message (include a timestamp) to the console on each tick, and log once at startup confirming it's active and what interval it's using
- keep it self-contained, no new npm dependencies

After writing the file, print its full final contents so I can review it.
```

## Two real bugs, two rounds of self-debugging

**Bug 1 — missing service injection.** The first draft called
`ctx.interval(...)` directly. Cordis requires a plugin to declare which
mixed-in services it actually uses before accessing them; skipping that
throws `cannot get property "timer" without inject` and crashes the whole
harness boot (same chicken-and-egg problem as the TODO scanner: a crashing
plugin prevents the very agent that would fix it from starting, so it had
to be temporarily unregistered from `dsh.patch.yml` first). Prompted the
agent with the exact error and asked it to find the real pattern:

```
The file ./plugins/break-reminder/src/index.ts fails to load into DeepSeek Harness with this error:

Error: cannot get property "timer" without inject
    at new apply (.../plugins/break-reminder/src/index.ts:28:7)

The plugin calls ctx.interval(...) but Cordis requires a plugin to explicitly declare which mixed-in services it uses before accessing them — accessing ctx.interval without that declaration throws this error. Look at how other plugins declare a service dependency (search installed packages under .dsh-home/profiles/headless/node_modules/@deepseek-ai/ for the word 'inject' as an exported plugin property) and fix ./plugins/break-reminder/src/index.ts so it declares its dependency on the timer service correctly. Keep the rest of the plugin as-is. After fixing it, print the full final contents of the file.
```

It added `export const inject = ['timer']` — correct in isolation, but...

**Bug 2 — the fix didn't actually take effect**, same error again. The file
still ended with `export default { name, apply }`, which doesn't include
`inject` — the loader reads the default export as authoritative, so the
separately-exported `inject` constant was invisible to it. This one wasn't
handed to the agent as a ready-made fix — it was reported as a *diagnosis
to investigate*:

```
Your previous fix to ./plugins/break-reminder/src/index.ts added 'export const inject = ["timer"]' as a separate named export, but the SAME file still ends with 'export default { name, apply }' which does not include inject. The exact same error still happens:

Error: cannot get property "timer" without inject
    at new apply (.../plugins/break-reminder/src/index.ts:30:7)

My hypothesis: the module loader reads the default export object as the authoritative plugin definition, so it never sees the separately-exported inject constant since the default export object doesn't carry it. Fix the file so inject is actually part of whatever the loader reads — either by adding inject to the default export object, or by removing the default export entirely and relying only on the named exports (check the reference file ./plugins/_reference/cordis-plugin-timer.ts and how the official read-tool example in ./plugins/_reference/dsh-tool-fs-example.js export their plugins, to see which export style is actually correct). After fixing it, print the full final contents of the file.
```

It removed the conflicting default export, keeping only named exports
(`name`, `inject`, `apply`) — matching the reference files' real pattern —
and that was the actual fix.

## Demo

```bash
export DSH_HOME=./.dsh-home
set -a && source ../.env && set +a
npx --yes @deepseek-ai/dsh web --patch ./dsh.patch.yml --no-open
```

Default interval is 20 minutes. For a fast demo, apply a second overlay
that shortens it (any `--patch` file works; nothing needs to change in the
committed `dsh.patch.yml`):

```bash
cat > /tmp/break-reminder-test-overlay.yml << 'EOF'
- id: break-reminder
  config:
    intervalMinutes: 0.2
EOF
npx --yes @deepseek-ai/dsh web --patch ./dsh.patch.yml --patch /tmp/break-reminder-test-overlay.yml --no-open
```

Verified result: the startup line
(`[break-reminder] Plugin activated. Reminding every 0.2 minutes.`)
appeared immediately, and the reminder fired twice, 12 seconds apart
(`11:11:30 PM` and `11:11:42 PM`) — exact, repeating, matching the
configured interval precisely.
