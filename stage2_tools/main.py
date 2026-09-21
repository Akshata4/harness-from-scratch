import json
import os
import sys

from dotenv import find_dotenv, load_dotenv
from llm_client import get_client_and_model
from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

load_dotenv(find_dotenv())

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to tools for reading files and "
    "listing directories. Use them when you need real information instead "
    "of guessing."
)


def main() -> None:
    prompt = " ".join(sys.argv[1:]) or (
        "What files are in the stage0_single_call directory, and what does main.py do?"
    )

    client, model = get_client_and_model()
    provider = os.environ.get("LLM_PROVIDER", "openrouter")
    print(f"[provider={provider} model={model}]\n")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    response = client.chat.completions.create(model=model, messages=messages, tools=TOOL_SCHEMAS)
    assistant_message = response.choices[0].message

    tool_calls = assistant_message.tool_calls
    if not tool_calls:
        print(assistant_message.content)
        return

    messages.append(assistant_message.model_dump(exclude_none=True))

    for call in tool_calls:
        fn_name = call.function.name
        args = json.loads(call.function.arguments)
        print(f"[tool call] {fn_name}({args})")

        result = TOOL_FUNCTIONS[fn_name](**args)
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    final_response = client.chat.completions.create(model=model, messages=messages, tools=TOOL_SCHEMAS)
    final_message = final_response.choices[0].message

    if final_message.tool_calls:
        wanted = [c.function.name for c in final_message.tool_calls]
        print(
            f"\n[the model asked for another tool call ({wanted}) but this stage "
            "only allows a single round trip — see Stage 3 for a real loop]"
        )
    else:
        print(f"\n{final_message.content}")


if __name__ == "__main__":
    main()
