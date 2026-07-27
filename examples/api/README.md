# Hy3 API examples

These examples provide small, standalone OpenAI-compatible API clients for Hy3. Start with the repository [API quickstart](../../quickstart.md) to configure an endpoint and receive the first response.

## Setup

From the repository root, install the client dependency in a dedicated virtual environment:

```bash
python -m pip install -r examples/api/requirements.txt
```

Configure `HY3_PROVIDER`, `HY3_BASE_URL`, `HY3_API_KEY`, and `HY3_MODEL` as described in the [API quickstart](../../quickstart.md). Never place a real API key in an example, terminal output shared with others, or a Git commit.

## Available examples

| Script | What it demonstrates |
| --- | --- |
| `basic_chat.py` | Single-turn chat, explicit multi-turn history, and basic response parsing |
| `streaming.py` | Streaming output, incremental content parsing, finish reason, and usage reporting |
| `latency_compare.py` | Single-run comparison of non-streaming total latency and streaming TTFT and total latency |

## Run an example

Run examples from the repository root:

```bash
python examples/api/basic_chat.py
```

### Verified outputs

Unless otherwise noted, the following outputs were verified on 2026-07-27 using TokenHub Guangzhou (`model=hy3`), Python 3.11.9, and OpenAI Python SDK 2.48.0.

#### `basic_chat.py`

```text
Provider: tokenhub
Model: hy3

Single-turn response
An API (Application Programming Interface) is a set of rules and protocols that lets different software applications communicate and exchange data with each other.
finish_reason: stop
tokens: prompt=24, completion=28, total=52

Multi-turn follow-up
For example, when a travel app like Kayak uses a flight booking API from an airline to fetch real-time flight prices and seat availability, it can show users options without accessing the airline's internal database directly.
finish_reason: stop
tokens: prompt=62, completion=44, total=106
```

#### `streaming.py`

```text
Provider: tokenhub
Model: hy3

Streaming response
content: 1. **Use a single configured client instance** – centralize base URL, timeouts, and auth so changes happen in one place.
2. **Isolate API details behind a thin wrapper** – expose domain-friendly methods, not raw HTTP calls, to reduce coupling.
3. **Handle and surface errors consistently** – map HTTP/network failures to clear, typed exceptions for predictable debugging.
chunks_received: 50
finish_reason: stop
tokens: prompt=26, completion=81, total=107
```

#### `latency_compare.py`

Verified on 2026-07-28 using the same environment. This is a single-run client observation, not a benchmark.

```text
Provider: tokenhub
Model: hy3
Measurement: single-run client observation, not a benchmark
Streaming TTFT: time to first non-empty content chunk

Non-streaming
ttft_seconds: unavailable (buffered response)
total_seconds: 2.265
characters: 202
finish_reason: stop
tokens: prompt=29, completion=35, total=64

Streaming
ttft_seconds: 0.710
total_seconds: 1.364
characters: 236
finish_reason: stop
tokens: prompt=29, completion=38, total=67
```

## Design conventions

- Each script is standalone and can be copied without importing a project-specific helper module.
- Connection settings and credentials come from environment variables.
- Scripts never print the API key.
- Responses are parsed explicitly instead of printing the complete SDK object.
- Provider-specific request fields are used only by examples that need them.
- Sample output is added only after the corresponding example has been verified against a real Hy3 endpoint.

The client setup has been checked with Python 3.11.9 and OpenAI Python SDK 2.48.0. Live provider, date, and onboarding results are recorded in the Pull Request description.
