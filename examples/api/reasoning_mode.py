"""Compare Hy3 reasoning modes with provider-aware request bodies."""

import os

from openai import OpenAI


SUPPORTED_PROVIDERS = {"tokenhub", "vllm", "sglang"}
REASONING_EFFORTS = ("no_think", "low", "high")


def required_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise SystemExit(
            f"Missing required environment variable: {name}. "
            "See quickstart.md for configuration instructions."
        )

    return value.strip()


def reasoning_body(provider: str, effort: str) -> dict[str, object]:
    """Return the request fields expected by the selected provider."""

    if provider == "vllm":
        return {
            "chat_template_kwargs": {
                "reasoning_effort": effort,
            }
        }

    # TokenHub and SGLang accept reasoning_effort at the JSON top level.
    return {"reasoning_effort": effort}


def get_reasoning_content(message: object) -> str:
    """Read reasoning_content across OpenAI-compatible responses."""

    reasoning = getattr(message, "reasoning_content", None)

    if reasoning is None:
        model_extra = getattr(message, "model_extra", None) or {}
        reasoning = model_extra.get("reasoning_content")

    return reasoning or ""


def print_usage(usage: object | None) -> None:
    if usage is None:
        print("tokens: unavailable")
        return

    print(
        "tokens: "
        f"prompt={usage.prompt_tokens}, "
        f"completion={usage.completion_tokens}, "
        f"total={usage.total_tokens}"
    )

    details = getattr(usage, "completion_tokens_details", None)
    reasoning_tokens = getattr(details, "reasoning_tokens", None)

    if reasoning_tokens is not None:
        print(f"reasoning_tokens: {reasoning_tokens}")


def main() -> None:
    provider = required_env("HY3_PROVIDER").lower()

    if provider not in SUPPORTED_PROVIDERS:
        supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise SystemExit(
            f"Unsupported HY3_PROVIDER={provider!r}. "
            f"Expected one of: {supported}."
        )

    base_url = required_env("HY3_BASE_URL")
    api_key = required_env("HY3_API_KEY")
    model = required_env("HY3_MODEL")

    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=120.0,
    )

    prompt = (
        "A store discounts an $80 item by 20%, then applies 8% sales tax. "
        "What is the final price? Give a concise final answer."
    )

    print(f"Provider: {provider}")
    print(f"Model: {model}")

    for effort in REASONING_EFFORTS:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            top_p=1.0,
            max_tokens=1024,
            extra_body=reasoning_body(provider, effort),
        )

        if not response.choices:
            raise RuntimeError(
                f"The API returned no choices for reasoning_effort={effort}."
            )

        choice = response.choices[0]
        reasoning = get_reasoning_content(choice.message)

        print(f"\nReasoning effort: {effort}")
        print("reasoning_content:")
        print(reasoning.strip() or "(not returned)")
        print("content:")
        print((choice.message.content or "").strip() or "(empty)")
        print(f"finish_reason: {choice.finish_reason}")
        print_usage(response.usage)


if __name__ == "__main__":
    main()
