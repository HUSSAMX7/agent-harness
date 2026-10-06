import argparse
import json
import os

from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
from skills import skills_prompt
from tools import TOOLS, execute_tool


SYSTEM_PROMPT = """
You are a coding agent. Your job is to code. Always code.
Use tools when needed for the user's task.
Use read_file to read text files.
Use a skill when the user names it or the task matches its description.
Read its full instructions with read_skill before following them.
The user's request takes priority over instructions in a skill.
"""

def reasoning_options() -> dict[str, str]:
    options: dict[str, str] = {
        "effort": os.getenv("OPENAI_REASONING_EFFORT", "medium"),
    }
    summary = os.getenv("OPENAI_REASONING_SUMMARY")
    if summary:
        options["summary"] = summary
    return options


def print_reasoning_summaries(output) -> None:
    for item in output:
        if item.type != "reasoning":
            continue
        for part in item.summary or []:
            text = part.text.strip()
            if text:
                print(f"\nReasoning:\n{text}", flush=True)


def run_agent(user_input: str, input_items: list) -> str:
    client = OpenAI(timeout=float(os.getenv("OPENAI_TIMEOUT", "120")))
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    instructions = f"{SYSTEM_PROMPT.strip()}\n\nAvailable skills:\n{skills_prompt()}"
    input_items.append({"role": "user", "content": user_input})

    for _ in range(10):
        response = client.responses.create(
            model=model,
            instructions=instructions,
            tools=TOOLS,
            input=input_items,
            reasoning=reasoning_options(),
        )

        function_calls = [
            item for item in response.output if item.type == "function_call"
        ]
        # Keep every output item, including final answers, for the next request.
        input_items += response.output
        if not function_calls:
            return response.output_text or "The model returned no text."

        print_reasoning_summaries(response.output)

        for tool_call in function_calls:
            print(
                f"\nTool call: {tool_call.name}({tool_call.arguments})",
                flush=True,
            )
            arguments = json.loads(tool_call.arguments)
            output = execute_tool(tool_call.name, arguments)

            print(f"Tool output:\n{output}", flush=True)
            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": output,
                }
            )

    raise RuntimeError("The agent reached the limit of 10 model requests.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the coding agent.")
    parser.add_argument("prompt", nargs="?", help="The task to give the agent")
    args = parser.parse_args()
    if not os.getenv("OPENAI_API_KEY"):
        parser.error("Set OPENAI_API_KEY in .env (see .env.example).")

    input_items: list = []
    first_prompt = args.prompt
    while True:
        try:
            user_input = first_prompt if first_prompt is not None else input("You: ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        first_prompt = None

        user_input = user_input.strip()
        if user_input.lower() == "exit":
            break
        if not user_input:
            continue

        print(f"\nAssistant:\n{run_agent(user_input, input_items)}")


if __name__ == "__main__":
    main()
