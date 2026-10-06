"""The current plan lives in memory and is re-injected before each model request."""

MARKS = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]"}

TODOS: list[dict[str, str]] = []


def write_todos(todos: list[dict[str, str]]) -> str:
    """Replace the whole list. At most one task may be in_progress."""
    if not isinstance(todos, list):
        return "Error: todos must be a list."

    for index, todo in enumerate(todos, start=1):
        if not isinstance(todo, dict):
            return f"Error: task {index} must be an object."
        for field in ("content", "activeForm", "status"):
            value = todo.get(field)
            if not isinstance(value, str) or not value.strip():
                return f"Error: task {index} needs a non-empty string for {field}."
        if todo["status"] not in MARKS:
            return f"Error: task {index} has an invalid status: {todo['status']}."

    active = [todo for todo in todos if todo["status"] == "in_progress"]
    if len(active) > 1:
        return f"Error: {len(active)} tasks are in_progress. Only one may be."

    TODOS[:] = todos
    return todos_prompt() or "Todo list cleared."


def todos_prompt() -> str:
    return "\n".join(f"{MARKS[todo['status']]} {todo['content']}" for todo in TODOS)


def active_form() -> str:
    """Return what the agent is doing, for a future spinner."""
    for todo in TODOS:
        if todo["status"] == "in_progress":
            return todo["activeForm"]
    return "thinking"


TODO_SCHEMA = {
    "type": "function",
    "name": "write_todos",
    "description": (
        "Record the plan for a multi-step task. Send the whole list every "
        "time. Keep at most one task in_progress and update the plan when "
        "a step starts, finishes, or changes. Send an empty list to clear it."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The task, imperative: 'Fix the parser'",
                        },
                        "activeForm": {
                            "type": "string",
                            "description": "Present continuous: 'Fixing the parser'",
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "done"],
                        },
                    },
                    "required": ["content", "activeForm", "status"],
                },
            }
        },
        "required": ["todos"],
    },
    "strict": False,
}
