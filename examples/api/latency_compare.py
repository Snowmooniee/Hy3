"""Compare client-observed non-streaming and streaming latency for Hy3."""

import os
from time import perf_counter

from openai import OpenAI


def required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise SystemExit(f"{name} is not set. See quickstart.md.")
    return value


def usage_summary(usage) -> str:
    if usage is None:
        return "unavailable"

    return (
        f"prompt={usage.prompt_tokens}, "
        f"completion={usage.completion_tokens}, "
        f"total={usage.total_tokens}"
    )


def main() -> None:
    provider = required_env("HY3_PROVIDER").strip().lower()
    base_url = required_env("HY3_BASE_URL").strip()
    api_key = required_env("HY3_API_KEY")
    model = required_env("HY3_MODEL").strip()

    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=60.0,
        max_retries=0,
    )
    request = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Give exactly three short bullet points explaining "
                    "why API request timeouts matter."
                ),
            }
        ],
        "temperature": 0.9,
        "top_p": 1.0,
        "max_tokens": 160,
    }

    started = perf_counter()
    response = client.chat.completions.create(**request)
    non_streaming_total = perf_counter() - started

    if (
        not response.choices
        or not response.choices[0].message.content
        or response.choices[0].finish_reason is None
    ):
        raise RuntimeError("The non-streaming response was incomplete.")

    non_streaming_choice = response.choices[0]
    non_streaming_content = non_streaming_choice.message.content

    started = perf_counter()
    stream = client.chat.completions.create(
        **request,
        stream=True,
        stream_options={"include_usage": True},
    )

    first_content_seconds = None
    content_parts = []
    finish_reason = None
    streaming_usage = None

    for chunk in stream:
        if chunk.usage is not None:
            streaming_usage = chunk.usage

        if not chunk.choices:
            continue

        choice = chunk.choices[0]
        content = choice.delta.content

        if content:
            if first_content_seconds is None:
                first_content_seconds = perf_counter() - started
            content_parts.append(content)

        if choice.finish_reason is not None:
            finish_reason = choice.finish_reason

    streaming_total = perf_counter() - started
    streaming_content = "".join(content_parts)

    if (
        not streaming_content
        or first_content_seconds is None
        or finish_reason is None
    ):
        raise RuntimeError("The streaming response was incomplete.")

    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print("Measurement: single-run client observation, not a benchmark")
    print("Streaming TTFT: time to first non-empty content chunk")

    print("\nNon-streaming")
    print("ttft_seconds: unavailable (buffered response)")
    print(f"total_seconds: {non_streaming_total:.3f}")
    print(f"characters: {len(non_streaming_content)}")
    print(f"finish_reason: {non_streaming_choice.finish_reason}")
    print(f"tokens: {usage_summary(response.usage)}")

    print("\nStreaming")
    print(f"ttft_seconds: {first_content_seconds:.3f}")
    print(f"total_seconds: {streaming_total:.3f}")
    print(f"characters: {len(streaming_content)}")
    print(f"finish_reason: {finish_reason}")
    print(f"tokens: {usage_summary(streaming_usage)}")


if __name__ == "__main__":
    main()