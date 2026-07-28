"""Handle Hy3 API errors with a bounded, explicit retry policy."""

import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
)


SUPPORTED_PROVIDERS = {"tokenhub", "vllm", "sglang"}
MAX_ATTEMPTS = 4
BASE_DELAY_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 8.0
MAX_RETRY_AFTER_SECONDS = 60.0

RETRYABLE_STATUS_CODES = {
    408,  # Request timeout
    429,  # Dynamic provider rate limit
    500,
    502,
    503,
    504,
}
FAST_FAIL_STATUS_CODES = {
    400,  # Invalid request
    401,  # Invalid or missing authentication
    403,  # Insufficient permission
}


def required_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise SystemExit(
            f"Missing required environment variable: {name}. "
            "See quickstart.md for configuration instructions."
        )

    return value.strip()


def retry_category(error: Exception) -> str | None:
    if isinstance(error, APITimeoutError):
        return "timeout"

    if isinstance(error, APIConnectionError):
        return "network"

    if (
        isinstance(error, APIStatusError)
        and error.status_code in RETRYABLE_STATUS_CODES
    ):
        return f"http_{error.status_code}"

    return None


def retry_after_seconds(error: APIStatusError) -> float | None:
    """Parse Retry-After as seconds or an HTTP date."""

    value = error.response.headers.get("retry-after")

    if value is None:
        return None

    try:
        return max(0.0, float(value))
    except ValueError:
        pass

    try:
        retry_at = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None

    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)

    return max(
        0.0,
        (retry_at - datetime.now(timezone.utc)).total_seconds(),
    )


def create_chat_completion(
    client: OpenAI,
    model: str,
) -> object:
    """Send one request using the example's retry policy."""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "In one sentence, explain how an API client "
                            "should handle a transient server error."
                        ),
                    }
                ],
                temperature=0.9,
                top_p=1.0,
                max_tokens=128,
            )
        except (APIConnectionError, APIStatusError) as error:
            category = retry_category(error)

            if category is None:
                status_code = getattr(error, "status_code", None)

                if status_code in FAST_FAIL_STATUS_CODES:
                    print(
                        f"attempt {attempt}: HTTP {status_code} "
                        "is a fast-fail client or authentication error"
                    )
                else:
                    print(
                        f"attempt {attempt}: error is not retryable "
                        f"under this policy (status={status_code})"
                    )

                raise

            if attempt == MAX_ATTEMPTS:
                print(
                    f"attempt {attempt}: retryable {category} error; "
                    "retry budget exhausted"
                )
                raise

            retry_after = None

            if isinstance(error, APIStatusError):
                retry_after = retry_after_seconds(error)

            if retry_after is not None:
                if retry_after > MAX_RETRY_AFTER_SECONDS:
                    print(
                        f"attempt {attempt}: Retry-After={retry_after:.2f}s "
                        "exceeds the client safety limit; aborting"
                    )
                    raise

                delay = retry_after
                delay_source = "Retry-After"
            else:
                delay = min(
                    BASE_DELAY_SECONDS * (2 ** (attempt - 1)),
                    MAX_BACKOFF_SECONDS,
                )
                delay_source = "bounded exponential backoff"

            print(
                f"attempt {attempt}: retryable {category} error; "
                f"waiting {delay:.2f}s using {delay_source}"
            )
            time.sleep(delay)

    raise RuntimeError("Retry loop exited unexpectedly.")


def main() -> None:
    provider = required_env("HY3_PROVIDER").lower()

    if provider not in SUPPORTED_PROVIDERS:
        supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise SystemExit(
            f"Unsupported HY3_PROVIDER={provider!r}. "
            f"Expected one of: {supported}."
        )

    model = required_env("HY3_MODEL")
    client = OpenAI(
        base_url=required_env("HY3_BASE_URL"),
        api_key=required_env("HY3_API_KEY"),
        timeout=30.0,
        max_retries=0,
    )

    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"Maximum attempts: {MAX_ATTEMPTS}")

    response = create_chat_completion(client, model)

    if not response.choices:
        raise RuntimeError("The API returned no choices.")

    choice = response.choices[0]
    content = (choice.message.content or "").strip()

    if not content:
        raise RuntimeError("The assistant response was empty.")

    print("response:")
    print(content)
    print(f"finish_reason: {choice.finish_reason}")

    if response.usage is not None:
        print(
            "tokens: "
            f"prompt={response.usage.prompt_tokens}, "
            f"completion={response.usage.completion_tokens}, "
            f"total={response.usage.total_tokens}"
        )


if __name__ == "__main__":
    main()
