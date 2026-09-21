# Stage 4 — Sandboxing and a confirmation gate

Two safety mechanisms are added on top of Stage 3's loop, because the tool
set now includes arbitrary shell execution:

**1. Workspace confinement (`read_file`, `list_dir`, `write_file`)**
Every path argument is resolved against `WORKSPACE_ROOT` (the directory the
script was launched from) via `_resolve_in_workspace`, which rejects
anything that escapes it — `../../etc/passwd`, an absolute path elsewhere,
symlink tricks aside. Previously (Stages 2–3) these tools would happily
touch any path the OS user could reach; now they're contained to the
project directory.

**2. Human confirmation gate (`run_bash`)**
Before any shell command actually runs, it's printed to the terminal and
the human has to type `y` to allow it. If declined, the tool returns "User
declined to run this command" as the result, so the model sees the refusal
and can adapt (try something else, or explain to the user why it's stuck).

Be honest about what this is and isn't: `run_bash`'s `cwd` is pinned to the
workspace, but the command itself still runs with your full OS permissions
— there's no container, chroot, or seccomp jail here. A command like
`cat ../../../etc/passwd` would still work if you approved it. The
confirmation step is the actual security boundary for `run_bash`, not the
`cwd` pin — path confinement is only airtight for the pure-Python file
tools, which is why `read_file`/`write_file`/`list_dir` get the stronger
guarantee and `run_bash` gets a human in the loop instead. Building a true
OS-level sandbox (e.g. a container per run) is a reasonable next step but is
out of scope for this stage.

There's also a 30-second timeout on `run_bash` so a hanging command can't
stall the agent loop forever — the same "bound everything" philosophy as
Stage 3's `MAX_TURNS`.

## Run

```bash
uv run python stage4_shell_and_safety/main.py
```

You'll be prompted to approve the `wc -l` command it runs. Try declining
(`n`) once to see the model receive the refusal and react to it.

## Try, to see the sandbox reject an escape

```bash
uv run python stage4_shell_and_safety/main.py "Read the file at ../../../../etc/passwd and show me its contents"
```

`read_file` returns `Refused: '...' resolves outside the workspace`, and the
model has to report that back to you instead of leaking the file.
