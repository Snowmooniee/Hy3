"""Stream a Hy3 chat completion and parse the response chunks."""

import os

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


def main() -> None:
    """Stream one response and assemble its content."""
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

    stream = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": (
                    "Give three concise tips for writing "
                    "maintainable API clients."
                ),
            }
        ],
        temperature=0.9,
        top_p=1.0,
        stream=True,
        stream_options={"include_usage": True},
    )

    content_parts = []
    finish_reason = None
    usage = None
    chunk_count = 0

    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print("\nStreaming response")
    print("content: ", end="", flush=True)

    for chunk in stream:
        chunk_count += 1

        if chunk.usage is not None:
            usage = chunk.usage

        if not chunk.choices:
            continue

        choice = chunk.choices[0]
        content = choice.delta.content

        if content:
            content_parts.append(content)
            print(content, end="", flush=True)

        if choice.finish_reason is not None:
            finish_reason = choice.finish_reason

    print()

    complete_content = "".join(content_parts)
    if not complete_content:
        raise RuntimeError("The stream returned no assistant content.")

    if finish_reason is None:
        raise RuntimeError("The stream ended without a finish reason.")

    print(f"chunks_received: {chunk_count}")
    print(f"finish_reason: {finish_reason}")

    if usage is None:
        print("tokens: unavailable")
    else:
        print(
            "tokens: "
            f"prompt={usage.prompt_tokens}, "
            f"completion={usage.completion_tokens}, "
            f"total={usage.total_tokens}"
        )


if __name__ == "__main__":
    main()