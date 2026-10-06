---
name: harness-development
description: Extend or explain this repository's coding-agent harness, including tools, skill discovery, or conversation state.
---

# Harness development

Use the official OpenAI SDK directly. Keep the harness free of agent frameworks.
Prefer functions; introduce a class only when the required state or behavior
justifies it. Manage dependencies and run Python with `uv`.

Keep every model output item in conversation history, including final replies
and reasoning items. Pair each tool result with the original call's `call_id`.
The conversation lasts for the running process and ends when the user types
`exit`.

Keep skill discovery separate from loading instructions: expose names and
descriptions in the catalog; load a selected skill through `read_skill(name)`
when its instructions are needed.
