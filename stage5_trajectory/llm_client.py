import os

from openai import OpenAI

PROVIDER_DEFAULTS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "deepseek/deepseek-chat-v3.1",
    },
    "wandb": {
        "base_url": "https://api.inference.wandb.ai/v1",
        "model": "meta-llama/Llama-3.1-8B-Instruct",
    },
}


def get_client_and_model() -> tuple[OpenAI, str]:
    """Both OpenRouter and W&B Inference speak the OpenAI chat-completions
    schema, so the only thing that changes between them is base_url/api_key
    (and W&B's project field). Same client code either way."""
    provider = os.environ.get("LLM_PROVIDER", "openrouter").lower()
    if provider not in PROVIDER_DEFAULTS:
        raise ValueError(f"Unknown LLM_PROVIDER={provider!r}; use 'openrouter' or 'wandb'")

    defaults = PROVIDER_DEFAULTS[provider]
    model = os.environ.get("LLM_MODEL") or defaults["model"]

    if provider == "openrouter":
        client = OpenAI(
            base_url=defaults["base_url"],
            api_key=os.environ["OPENROUTER_API_KEY"],
            default_headers={
                "HTTP-Referer": "https://github.com/local/harness-from-scratch",
                "X-Title": "harness-from-scratch",
            },
        )
    else:  # wandb
        client = OpenAI(
            base_url=defaults["base_url"],
            api_key=os.environ["WANDB_API_KEY"],
            project=os.environ["WANDB_PROJECT"],
        )

    return client, model
