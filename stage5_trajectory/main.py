import json
import os
import sys

from dotenv import find_dotenv, load_dotenv
from llm_client import get_client_and_model
from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS
from trajectory import Trajectory, replay_file

load_dotenv(find_dotenv())

SYSTEM_PROMPT = (
    "You are a helpful coding assistant with access to tools for reading "
    "files, listing directories, writing files, and running shell commands "
    "(run_bash requires human confirmation before it executes, so expect it "
    "to sometimes be declined). Use tools whenever you need real information "
    "or need to make a change, and keep going until the task is fully done. "
    "Once finished, reply with a normal message and no further tool calls."
)

MAX_TURNS = 8


def run(prompt: str) -> None:
    client, model = get_client_and_model()
    provider = os.environ.get("LLM_PROVIDER", "openrouter")
    print(f"[provider={provider} model={model}]\n")

    trajectory = Trajectory(provider, model)
    trajectory.log_system(SYSTEM_PROMPT)
    trajectory.log_user(prompt)
    print(f"[trajectory] logging this run to {trajectory.path}\n")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    for turn in range(1, MAX_TURNS + 1):
        response = client.chat.completions.create(model=model, messages=messages, tools=TOOL_SCHEMAS)
        assistant_message = response.choices[0].message
        messages.append(assistant_message.model_dump(exclude_none=True))

        tool_calls_log = None
        if assistant_message.tool_calls:
            tool_calls_log = [
                {"id": c.id, "name": c.function.name, "args": json.loads(c.function.arguments)}
                for c in assistant_message.tool_calls
            ]
        trajectory.log_assistant(assistant_message.content, tool_calls_log)

        if not assistant_message.tool_calls:
            print(assistant_message.content)
            trajectory.close()
            return

        for call in assistant_message.tool_calls:
            fn_name = call.function.name
            args = json.loads(call.function.arguments)
            print(f"[turn {turn}] tool call: {fn_name}({args})")

            result = TOOL_FUNCTIONS[fn_name](**args)
            preview = result if len(result) <= 300 else result[:300] + " [truncated]"
            print(f"    -> {preview}")

            trajectory.log_tool_result(fn_name, args, result)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    print(f"\n[stopped after {MAX_TURNS} turns without a final answer]")
    trajectory.close()


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "--replay":
        replay_file(sys.argv[2])
        return

    prompt = " ".join(sys.argv[1:]) or (
        "List the files in stage0_single_call, then run "
        "`wc -l stage0_single_call/main.py` and tell me how many lines it has."
    )
    run(prompt)


if __name__ == "__main__":
    main()
