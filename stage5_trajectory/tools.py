import os
import subprocess

WORKSPACE_ROOT = os.path.abspath(os.getcwd())
BASH_TIMEOUT_SECONDS = 30

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full text contents of a file, given a path relative to the workspace root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file to read."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and folders inside a directory, given a path relative to the workspace root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the directory. Use '.' for the workspace root."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a file, given a path relative to the workspace root. Creates parent directories and overwrites existing files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file to write."},
                    "content": {"type": "string", "description": "Full text content to write to the file."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_bash",
            "description": "Execute a shell command in the workspace root. Requires human confirmation before it runs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute."},
                },
                "required": ["command"],
            },
        },
    },
]


def _resolve_in_workspace(path: str) -> str:
    """Resolve `path` against WORKSPACE_ROOT and reject anything that
    escapes it (via '..' or an absolute path elsewhere)."""
    full = os.path.abspath(os.path.join(WORKSPACE_ROOT, path))
    if os.path.commonpath([full, WORKSPACE_ROOT]) != WORKSPACE_ROOT:
        raise ValueError(f"'{path}' resolves outside the workspace ({WORKSPACE_ROOT})")
    return full


def read_file(path: str) -> str:
    try:
        full = _resolve_in_workspace(path)
    except ValueError as e:
        return f"Refused: {e}"
    try:
        with open(full) as f:
            return f.read()
    except OSError as e:
        return f"Error reading {path}: {e}"


def list_dir(path: str) -> str:
    try:
        full = _resolve_in_workspace(path)
    except ValueError as e:
        return f"Refused: {e}"
    try:
        return "\n".join(sorted(os.listdir(full)))
    except OSError as e:
        return f"Error listing {path}: {e}"


def write_file(path: str, content: str) -> str:
    try:
        full = _resolve_in_workspace(path)
    except ValueError as e:
        return f"Refused: {e}"
    try:
        parent = os.path.dirname(full)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(full, "w") as f:
            f.write(content)
        return f"Wrote {len(content)} characters to {path}"
    except OSError as e:
        return f"Error writing {path}: {e}"


def run_bash(command: str) -> str:
    print(f"\n[confirmation required] the agent wants to run:\n    {command}\n")
    try:
        answer = input("Allow this command to run? [y/N] ").strip().lower()
    except EOFError:
        answer = "n"  # no stdin available (e.g. a non-interactive run) — fail closed, not crash
    if answer.lower() not in {"y", "yes"}:
        return "User declined to run this command."

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=BASH_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {BASH_TIMEOUT_SECONDS}s"

    output = (result.stdout + result.stderr).strip()
    return f"[exit code {result.returncode}]\n{output}"


TOOL_FUNCTIONS = {
    "read_file": read_file,
    "list_dir": list_dir,
    "write_file": write_file,
    "run_bash": run_bash,
}
