# agent-harness

A coding agent harness built from scratch with Python, `uv`, and the official
OpenAI SDK. No agent frameworks. Prefer functions; add classes only when needed.

Install dependencies and create your local configuration:

```powershell
uv sync
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. `OPENAI_MODEL` defaults to `gpt-4.1-mini`.
The harness uses the **Responses API** (`client.responses.create`) so reasoning
models (for example `gpt-5.6-luna`) can use tools and reasoning together.
`OPENAI_REASONING_EFFORT` defaults to `medium` (`none`, `low`, `high`, etc.).
Optional: `OPENAI_REASONING_SUMMARY=concise` to print reasoning summaries.
`.env` is ignored by Git. `main.py` loads `.env` from the project root on startup.

Try a task that needs a tool:

```powershell
uv run main.py "Use bash to list the current directory and read README.md, then summarize the project."
```

Or omit the prompt to enter it interactively:

```powershell
uv run main.py
```

The conversation continues until you type `exit` (case-insensitive).
Empty messages are skipped. Ctrl+C or end-of-input also closes the prompt.
A single in-memory list keeps user messages, model output, tool calls, and
tool results throughout the session. Each request sends that history back to
the model. Restarting the program starts a fresh conversation.

`main.py` runs the conversation loop and calls the Responses API. `tools.py`
contains the tool definitions, their implementations, and `execute_tool`.
Edit its `TOOLS` list to choose which tools are available to the model.
The model may reason, call tools, and answer. Tool output is sent back as
`function_call_output` items (reasoning items from the prior turn stay in
context). This repeats until the model answers, with a limit of 10 requests
per user message.

`context.py` adds a fresh `reminder()` at the end of each model request using
`input_items + [reminder()]`. It includes the current local time with its UTC
offset, the Git branch, and any previously read files that changed or became
unavailable. The reminder is temporary and is not added to conversation history.

Successful `read_file` and `read_skill` calls record the file's modification
time in `SEEN`. Before each model request, `stale_files()` compares those saved
timestamps with the current files. Changed files trigger a reminder to read
them again. A successful reread updates the timestamp and clears that file's
warning. Reads through Bash are not tracked.

`todo.py` keeps the current plan in memory. For multi-step tasks, the model calls
`write_todos` with the whole list of tasks, each containing `content`, `activeForm`,
and a `status` of `pending`, `in_progress`, or `done`. At most one task may be
`in_progress`; all-pending and all-done lists are also valid. Invalid updates
return an error without replacing the current plan. An empty list clears it.

`reminder()` includes the latest non-empty plan in a `<todos>` block before every
model request. The block is temporary; tool calls and their results still stay
in conversation history. Tool output displays the updated plan as `[ ]`, `[~]`,
and `[x]` in the terminal. The plan resets when the program restarts.
`active_form()` returns the active task's `activeForm` text, or `thinking` if none
is active; it is available for a future spinner, with no spinner UI added yet.

Try a read-only planning task:

```powershell
uv run main.py "Use write_todos to plan reading README.md and pyproject.toml, read both files, mark each step done, then summarize them."
```

`read_file` accepts a required `path` and returns the whole text file as UTF-8.
Relative paths start from the directory where you launched the program.
Absolute paths also work, for example `D:/python/agent-harness/README.md`.
Read failures return an error message to the model.

```powershell
uv run main.py "Use read_file to read README.md and summarize it."
```

Commands run through Bash in the directory where you launched the program.
On Windows, the default is Git Bash at `C:/Program Files/Git/bin/bash.exe`.
On other systems, Bash must be on `PATH`. Set `BASH_PATH` in `.env` to use
another installation. Commands have a 60-second timeout and return their
exit code, stdout, and stderr.

The tool executes commands directly on your machine. It can read, write, and
delete files with your user's permissions.

`skills.py` discovers skills in two directories:

- `.agents/skills/<skill-name>/SKILL.md` inside the directory where you launch
  the program.
- `~/.agents/skills/<skill-name>/SKILL.md` inside your user home directory.

These folders hold Markdown documents. Each file starts with YAML metadata:

```yaml
---
name: my-skill
description: Explain what the skill does and when to use it.
---
```

Write the skill's instructions after the metadata. `PyYAML` parses that header;
`find_skills()` builds a dictionary keyed by skill name. The catalog sent to
the model includes only names and descriptions. The model reads a selected
skill through `read_skill(name)`, which looks up its path and returns the full
file. Unknown names return a message identifying the missing skill.

`SKILLS = find_skills()` runs once at startup. Restart the program after adding
or changing skill metadata. Full instructions are read from disk on each
`read_skill` call. If the same name exists in both locations, the user-home
version wins because it is scanned last.

`harness-development` records this project's design choices. Try:

```powershell
uv run main.py "Use harness-development and explain how we should add another tool."
```
