import json
import os
import sys

from dotenv import find_dotenv, load_dotenv
from llm_client import get_client_and_model
from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

load_dotenv(find_dotenv())

SYSTEM_PROMPT = (
    "You are a helpful coding assistant with access to tools for reading "
    "files, listing directories, and writing files. Use tools whenever you "
    "need real information or need to make a change, and keep using them "
    "until the task is fully done. Once finished, reply with a normal "
    "message and no further tool calls."
)

MAX_TURNS = 8


def main() -> None:
    prompt = " ".join(sys.argv[1:]) or (
        "Read stage0_single_call/README.md, then write a one-paragraph summary "
        "of it to stage3_agent_loop/demo_output/summary.md"
    )

    client, model = get_client_and_model()
    provider = os.environ.get("LLM_PROVIDER", "openrouter")
    print(f"[provider={provider} model={model}]\n")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    for turn in range(1, MAX_TURNS + 1):
        response = client.chat.completions.create(model=model, messages=messages, tools=TOOL_SCHEMAS)
        assistant_message = response.choices[0].message
        messages.append(assistant_message.model_dump(exclude_none=True))

        if not assistant_message.tool_calls:
            print(assistant_message.content)
            return

        for call in assistant_message.tool_calls:
            fn_name = call.function.name
            args = json.loads(call.function.arguments)
            print(f"[turn {turn}] tool call: {fn_name}({args})")

            result = TOOL_FUNCTIONS[fn_name](**args)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    print(f"\n[stopped after {MAX_TURNS} turns without a final answer]")


if __name__ == "__main__":
    main()
