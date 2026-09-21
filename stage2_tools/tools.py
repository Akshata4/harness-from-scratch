import os

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full text contents of a file, given a path relative to the current working directory.",
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
            "description": "List files and folders inside a directory, given a path relative to the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the directory. Use '.' for the current directory."},
                },
                "required": ["path"],
            },
        },
    },
]


def read_file(path: str) -> str:
    try:
        with open(path) as f:
            return f.read()
    except OSError as e:
        return f"Error reading {path}: {e}"


def list_dir(path: str) -> str:
    try:
        return "\n".join(sorted(os.listdir(path)))
    except OSError as e:
        return f"Error listing {path}: {e}"


TOOL_FUNCTIONS = {
    "read_file": read_file,
    "list_dir": list_dir,
}
