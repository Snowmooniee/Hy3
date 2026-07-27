"""Run single-turn and multi-turn chat requests against a Hy3 endpoint."""

import os
from typing import Dict, List

from openai import OpenAI


SUPPORTED_PROVIDERS = ("tokenhub", "vllm", "sglang")


def required_env(name: str) -> str:
    """Return a required environment variable or exit with a clear message."""
    value = os.getenv(name)
    if value is None or not value.strip():
        raise SystemExit(
            f"{name} is not set. Configure it as described in quickstart.md."
        )
    return value


def create_chat(
    client: OpenAI,
    model: str,
    messages: List[Dict[str, str]],
):
    """Send a provider-neutral chat completion request."""
    return client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.9,
        top_p=1.0,
    )


def print_response(label: str, response) -> str:
    """Print the useful response fields and return the assistant content."""
    if not response.choices:
        raise RuntimeError("The API returned no completion choices.")

    choice = response.choices[0]
    content = choice.message.content

    if not content:
        raise RuntimeError("The API returned an empty assistant message.")

    print(f"\n{label}")
    print(content)
    print(f"finish_reason: {choice.finish_reason}")

    if response.usage is not None:
        print(
            "tokens: "
            f"prompt={response.usage.prompt_tokens}, "
            f"completion={response.usage.completion_tokens}, "
            f"total={response.usage.total_tokens}"
        )

    return content


def main() -> None:
    """Run one single-turn request followed by a multi-turn request."""
    provider = required_env("HY3_PROVIDER").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        supported = ", ".join(SUPPORTED_PROVIDERS)
        raise SystemExit(
            f"Unsupported HY3_PROVIDER={provider!r}. "
            f"Choose one of: {supported}."
        )

    base_url = required_env("HY3_BASE_URL").strip()
    api_key = required_env("HY3_API_KEY")
    model = required_env("HY3_MODEL").strip()

    client = OpenAI(base_url=base_url, api_key=api_key)

    print(f"Provider: {provider}")
    print(f"Model: {model}")

    first_user_message = {
        "role": "user",
        "content": "Explain what an API is in one sentence.",
    }
    single_turn_messages = [first_user_message]

    first_response = create_chat(client, model, single_turn_messages)
    first_answer = print_response("Single-turn response", first_response)

    multi_turn_messages = [
        first_user_message,
        {"role": "assistant", "content": first_answer},
        {
            "role": "user",
            "content": "Now give one practical example.",
        },
    ]

    second_response = create_chat(client, model, multi_turn_messages)
    print_response("Multi-turn follow-up", second_response)


if __name__ == "__main__":
    main()
