import os
import sys

from dotenv import find_dotenv, load_dotenv
from llm_client import get_client_and_model

load_dotenv(find_dotenv())


def main() -> None:
    prompt = " ".join(sys.argv[1:]) or "Say hello in one sentence and name the model you are."
    client, model = get_client_and_model()
    provider = os.environ.get("LLM_PROVIDER", "openrouter")

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    print(f"[provider={provider} model={model}]\n")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
