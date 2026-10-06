import os
import subprocess

from context import note_read
from skills import read_skill
from todo import TODO_SCHEMA, write_todos


BASH_TOOL = {
    "type": "function",
    "name": "bash",
    "description": "Run a shell command and return its output.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to run",
            }
        },
        "required": ["command"],
    },
    "strict": False,
}

READ_FILE_TOOL = {
    "type": "function",
    "name": "read_file",
    "description": "Read a text file and return its contents.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": (
                    "Absolute or relative file path. "
                    "On Windows, use C:/... or D:/... paths."
                ),
            }
        },
        "required": ["path"],
    },
    "strict": False,
}

READ_SKILL_TOOL = {
    "type": "function",
    "name": "read_skill",
    "description": "Read an available skill by name and return its full instructions.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The skill name from the available skills list",
            }
        },
        "required": ["name"],
    },
    "strict": False,
}

TOOLS = [BASH_TOOL, READ_FILE_TOOL, READ_SKILL_TOOL, TODO_SCHEMA]


def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        note_read(path)
        return content
    except (OSError, UnicodeError) as exc:
        return f"Error reading {path}: {exc}"


def bash(command: str) -> str:
    bash_path = os.getenv("BASH_PATH") or (
        r"C:\Program Files\Git\bin\bash.exe" if os.name == "nt" else "bash"
    )
    try:
        result = subprocess.run(
            [bash_path, "-c", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 60 seconds."

    output = result.stdout + result.stderr
    return f"Exit code: {result.returncode}\n{output}"


def execute_tool(name: str, arguments: dict) -> str:
    if name == "bash":
        return bash(arguments["command"])
    if name == "read_file":
        return read_file(arguments["path"])
    if name == "read_skill":
        return read_skill(arguments["name"])
    if name == "write_todos":
        return write_todos(arguments.get("todos"))
    return f"Error: unknown tool {name}"
