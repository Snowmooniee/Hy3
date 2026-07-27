"""Run a bounded Hy3 tool-calling loop with an allowlisted local tool."""

import json
import os

from openai import OpenAI


SUPPORTED_PROVIDERS = {"tokenhub", "vllm", "sglang"}
MAX_TOOL_ROUNDS = 3
MAX_TOOL_CALLS_PER_ROUND = 4

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather from local demonstration data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name, for example Beijing.",
                    }
                },
                "required": ["city"],
                "additionalProperties": False,
            },
        },
    }
]

DEMO_WEATHER = {
    "city": "Beijing",
    "temperature_c": 22,
    "condition": "sunny",
    "source": "local demonstration data",
}


def required_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise SystemExit(
            f"Missing required environment variable: {name}. "
            "See quickstart.md for configuration instructions."
        )

    return value.strip()


def tool_request_body(provider: str) -> dict[str, object]:
    if provider == "vllm":
        return {
            "chat_template_kwargs": {
                "reasoning_effort": "high",
                "interleaved_thinking": True,
            }
        }

    return {"reasoning_effort": "high"}


def get_reasoning_content(message: object) -> str | None:
    reasoning = getattr(message, "reasoning_content", None)

    if reasoning is None:
        model_extra = getattr(message, "model_extra", None) or {}
        reasoning = model_extra.get("reasoning_content")

    return reasoning


def assistant_history(message: object) -> dict[str, object]:
    """Preserve content, reasoning, and tool calls for the next round."""

    history: dict[str, object] = {
        "role": "assistant",
        "content": getattr(message, "content", None),
    }
    reasoning = get_reasoning_content(message)
    tool_calls = getattr(message, "tool_calls", None)

    if reasoning is not None:
        history["reasoning_content"] = reasoning

    if tool_calls:
        history["tool_calls"] = [
            tool_call.model_dump(exclude_none=True)
            for tool_call in tool_calls
        ]

    return history


def get_weather(arguments: dict[str, object]) -> dict[str, object]:
    if set(arguments) != {"city"}:
        raise ValueError("get_weather requires exactly one city argument.")

    city = arguments["city"]

    if not isinstance(city, str) or not city.strip():
        raise ValueError("city must be a non-empty string.")

    supported_names = {"beijing", "beijing, china", "北京"}

    if city.strip().casefold() not in supported_names:
        raise ValueError(
            "Local demonstration data is available only for Beijing."
        )

    return dict(DEMO_WEATHER)


TOOL_HANDLERS = {
    "get_weather": get_weather,
}


def execute_tool_call(
    tool_call: object,
) -> tuple[str, str, dict[str, object], dict[str, object]]:
    if getattr(tool_call, "type", None) != "function":
        raise RuntimeError("Only function tool calls are supported.")

    tool_call_id = getattr(tool_call, "id", None)
    function = getattr(tool_call, "function", None)
    name = getattr(function, "name", None)
    raw_arguments = getattr(function, "arguments", None)

    if not isinstance(tool_call_id, str) or not tool_call_id:
        raise RuntimeError("The tool call has no valid ID.")

    if name not in TOOL_HANDLERS:
        raise RuntimeError(f"Refusing non-allowlisted tool: {name!r}.")

    if not isinstance(raw_arguments, str):
        raise RuntimeError("Tool arguments must be a JSON string.")

    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Tool {name!r} returned invalid JSON arguments."
        ) from error

    if not isinstance(arguments, dict):
        raise RuntimeError("Tool arguments must decode to a JSON object.")

    result = TOOL_HANDLERS[name](arguments)
    return tool_call_id, name, arguments, result


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
        timeout=120.0,
    )
    messages: list[dict[str, object]] = [
        {
            "role": "system",
            "content": (
                "Use get_weather for weather questions. Never invent weather. "
                "After receiving tool data, answer in one concise sentence."
            ),
        },
        {
            "role": "user",
            "content": "What is the weather in Beijing?",
        },
    ]

    executed = 0

    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"Maximum tool rounds: {MAX_TOOL_ROUNDS}")

    for round_number in range(1, MAX_TOOL_ROUNDS + 1):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.9,
            top_p=1.0,
            max_tokens=1024,
            extra_body=tool_request_body(provider),
        )

        if not response.choices:
            raise RuntimeError("The API returned no choices.")

        choice = response.choices[0]
        message = choice.message
        reasoning = get_reasoning_content(message)
        tool_calls = message.tool_calls or []

        messages.append(assistant_history(message))

        print(f"\nAPI round: {round_number}")
        print(f"finish_reason: {choice.finish_reason}")
        print(
            "reasoning_content_preserved: "
            f"{reasoning is not None}"
        )

        if not tool_calls:
            if executed == 0:
                raise RuntimeError(
                    "The model returned no tool call for the weather request."
                )

            final_answer = (message.content or "").strip()

            if not final_answer:
                raise RuntimeError("The final assistant response was empty.")

            print("final_answer:")
            print(final_answer)
            print(f"tool_calls_executed: {executed}")
            return

        if len(tool_calls) > MAX_TOOL_CALLS_PER_ROUND:
            raise RuntimeError("Per-round tool-call limit exceeded.")

        for tool_call in tool_calls:
            tool_call_id, name, arguments, result = execute_tool_call(
                tool_call
            )
            executed += 1

            print(f"tool: {name}")
            print(
                "arguments: "
                f"{json.dumps(arguments, ensure_ascii=False)}"
            )
            print(
                "result: "
                f"{json.dumps(result, ensure_ascii=False)}"
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(
                        result,
                        ensure_ascii=False,
                    ),
                }
            )

    raise RuntimeError(
        f"Tool loop exceeded the maximum of {MAX_TOOL_ROUNDS} rounds."
    )


if __name__ == "__main__":
    main()
