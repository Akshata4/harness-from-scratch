import os

from dotenv import find_dotenv, load_dotenv
from llm_client import get_client_and_model

load_dotenv(find_dotenv())

SYSTEM_PROMPT = "You are a helpful assistant. Keep answers concise."


def main() -> None:
    client, model = get_client_and_model()
    provider = os.environ.get("LLM_PROVIDER", "openrouter")
    print(f"[provider={provider} model={model}] Type 'exit' or Ctrl+D to quit.\n")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(model=model, messages=messages)
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})

        print(f"assistant> {reply}\n")


if __name__ == "__main__":
    main()
