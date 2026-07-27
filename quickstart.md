# Hy3 API Quickstart

Use this guide to make your first Hy3 API call and explore its core API capabilities. If you already have a TokenHub API key or a running self-hosted endpoint, you should be able to receive your first response within 5 minutes.

## Choose an access path

Choose one API access path before setting up the client:

| Path | Use it when | Required before you start |
| --- | --- | --- |
| TokenHub | You want to call Hy3 without deploying the model locally | A Tencent Cloud account with TokenHub access, an API key authorized for Hy3, and the base URL for your service region |
| Self-hosted API | You or your organization already operates Hy3 with vLLM or SGLang | A running OpenAI-compatible endpoint and its served model name |

This guide assumes that the TokenHub service or self-hosted endpoint is already available. Account provisioning, model download, and server deployment are outside the 5-minute first-call path.

For self-hosted deployment instructions, see [Deployment](./README.md#deployment).

## Set up the client environment

Create a dedicated virtual environment from the repository root. If another virtual environment is active, deactivate it before continuing.

### Linux and macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r examples/api/requirements.txt
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\examples\api\requirements.txt
```

These commands install only the client dependencies required by the API examples. They do not download the Hy3 model weights or start an inference server.

## Configure the API connection

The examples read their connection settings from environment variables. This keeps credentials out of source code and allows the same examples to connect to TokenHub or a self-hosted server.

### Environment variables

| Variable | Description |
| --- | --- |
| `HY3_PROVIDER` | Provider-specific request behavior: `tokenhub`, `vllm`, or `sglang` |
| `HY3_BASE_URL` | OpenAI-compatible API base URL, including `/v1` |
| `HY3_API_KEY` | TokenHub API key, or `EMPTY` for a self-hosted server without authentication |
| `HY3_MODEL` | Model or served model name used in API requests |

For TokenHub in Guangzhou, set the variables for the current terminal session:

```bash
export HY3_PROVIDER="tokenhub"
export HY3_BASE_URL="https://tokenhub.tencentmaas.com/v1"
export HY3_API_KEY="YOUR_API_KEY"
export HY3_MODEL="hy3"
```

On Windows PowerShell:

```powershell
$env:HY3_PROVIDER="tokenhub"
$env:HY3_BASE_URL="https://tokenhub.tencentmaas.com/v1"
$env:HY3_API_KEY="YOUR_API_KEY"
$env:HY3_MODEL="hy3"
```

Replace `YOUR_API_KEY` locally. Never place a real API key in this file, an example script, terminal output shared with others, or a Git commit.

TokenHub users in Singapore should use `https://tokenhub-intl.tencentmaas.com/v1`. Self-hosted users should select their connection values from the matrix below.

## Send your first request

The basic request below intentionally avoids provider-specific reasoning options. It works as the common starting point for TokenHub, vLLM, and SGLang.

### curl

The following command uses Bash syntax. Windows PowerShell users can use the Python example below.

```bash
curl "$HY3_BASE_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $HY3_API_KEY" \
  -d '{
    "model": "hy3",
    "messages": [
      {
        "role": "user",
        "content": "Introduce Hy3 in one sentence."
      }
    ],
    "temperature": 0.9,
    "top_p": 1.0
  }'
```

### Python OpenAI SDK

```python
import os

from openai import OpenAI


client = OpenAI(
    base_url=os.environ["HY3_BASE_URL"],
    api_key=os.environ["HY3_API_KEY"],
)

response = client.chat.completions.create(
    model=os.getenv("HY3_MODEL", "hy3"),
    messages=[
        {
            "role": "user",
            "content": "Introduce Hy3 in one sentence.",
        }
    ],
    temperature=0.9,
    top_p=1.0,
)

choice = response.choices[0]
print(f"Assistant: {choice.message.content}")
print(f"Finish reason: {choice.finish_reason}")

if response.usage is not None:
    print(f"Prompt tokens: {response.usage.prompt_tokens}")
    print(f"Completion tokens: {response.usage.completion_tokens}")
    print(f"Total tokens: {response.usage.total_tokens}")
```

## Parse the response

An OpenAI-compatible chat completion returns a `choices` list. For a basic request, inspect the first choice:

| Field | Meaning |
| --- | --- |
| `choice.message.content` | The assistant's generated text |
| `choice.finish_reason` | Why generation stopped, such as `stop` or `length` |
| `response.usage` | Token usage when the provider returns it |

The `usage` field may be unavailable on some compatible endpoints, so the Python example checks it before reading its token counts. Reasoning content, streaming chunks, and tool calls require different parsing and are covered by the corresponding examples.

## Common parameters

| Parameter | Purpose | Hy3 guidance |
| --- | --- | --- |
| `temperature` | Controls sampling randomness | Start with the repository-recommended value `0.9` |
| `top_p` | Controls nucleus sampling | Start with the repository-recommended value `1.0` |
| `max_tokens` | Limits the tokens generated for the request | Choose a value appropriate for the task and the limits enforced by the selected endpoint |
| `stop` | Stops generation when a specified string or one of several strings is reached | Set it only when the application has an explicit stopping sequence |
| `tools` | Provides OpenAI-compatible function definitions that the model may request | The application must validate and execute the selected function; self-hosted servers also require the documented tool-call parser |
| `stream` | Returns incremental chat-completion chunks instead of waiting for the complete response | Use it for interactive applications and parse every chunk before assembling the final response |

Supported values, defaults, and limits can vary between providers and serving configurations. This guide uses the repository-recommended values only for `temperature` and `top_p`; it does not assume repository-wide defaults for the other fields.

Reasoning fields are provider-specific; use the matching request shape below.

## Provider compatibility

Connection settings:

| Provider | `HY3_PROVIDER` | Base URL | API key | Model |
| --- | --- | --- | --- | --- |
| TokenHub (Guangzhou) | `tokenhub` | `https://tokenhub.tencentmaas.com/v1` | Required | `hy3` |
| TokenHub (Singapore) | `tokenhub` | `https://tokenhub-intl.tencentmaas.com/v1` | Required | `hy3` |
| vLLM, using this repository's deployment command | `vllm` | `http://127.0.0.1:8000/v1` | `EMPTY`, unless deployment authentication was added | `hy3` |
| SGLang, using this repository's deployment command | `sglang` | `http://127.0.0.1:8000/v1` | `EMPTY`, unless deployment authentication was added | `hy3` |

### Reasoning modes

Hy3 supports `no_think` for direct responses, `low` for reduced reasoning effort, and `high` for deeper reasoning on complex tasks. The repository default is `no_think`.

Choose exactly one Python SDK request shape:

| Provider | Python SDK `extra_body` | Required server configuration for advanced examples |
| --- | --- | --- |
| TokenHub | `{"reasoning_effort": effort}` | Managed by TokenHub |
| vLLM | `{"chat_template_kwargs": {"reasoning_effort": effort}}` | Use `--reasoning-parser hy_v3`; tool calling also requires `--tool-call-parser hy_v3` and `--enable-auto-tool-choice` |
| SGLang | `{"reasoning_effort": effort}` | When following this repository's deployment command, use `--reasoning-parser hunyuan` and `--tool-call-parser hunyuan` |

Replace `effort` with `no_think`, `low`, or `high`. For TokenHub and SGLang, `extra_body` adds `reasoning_effort` at the top level of the JSON request; for vLLM, it remains nested under `chat_template_kwargs`.

Do not combine the top-level and nested forms. Use only the request shape listed for the selected provider.

## Rate limits

This repository does not define a fixed requests-per-minute or tokens-per-minute limit. TokenHub limits vary by account, plan, model service, region, and platform policy; self-hosted limits depend on hardware, server configuration, concurrency, and any gateway in front of the endpoint.

When the API returns HTTP `429`, reduce the request rate and honor `Retry-After` when present. The retry example demonstrates bounded handling without assuming a fixed repository-wide limit.

## Run the examples

Example scripts use the same `HY3_PROVIDER`, `HY3_BASE_URL`, `HY3_API_KEY`, and `HY3_MODEL` environment variables configured above.

Start with the basic chat example from the repository root:

```bash
python examples/api/basic_chat.py
```

See the [API examples guide](./examples/api/README.md) for the available examples, expected behavior, and provider-specific notes.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| A missing environment variable or Python `KeyError` | Confirm that all four `HY3_*` variables are set in the current terminal session |
| Connection error or timeout | Confirm that the endpoint is reachable and that a self-hosted server is running |
| HTTP `400` | Check the request fields and make sure the reasoning or tool configuration matches the selected provider |
| HTTP `401` or `403` | Check the API key, account permissions, region, and endpoint; do not retry unchanged credentials |
| HTTP `404` or model-not-found error | Confirm that the base URL includes `/v1` and that `HY3_MODEL` matches the served model name |
| HTTP `429` | Reduce the request rate and honor `Retry-After` when present |
| Recoverable HTTP `5xx` | Retry with bounded backoff; do not retry indefinitely |

Retry only timeouts, connection failures, HTTP `429`, and recoverable `5xx` responses. Treat HTTP `400`, `401`, and `403` as configuration or request errors and fail fast.

## Further reading

- [Hy3 deployment instructions](./README.md#deployment)
- [Hy3 API examples](./examples/api/README.md)
- [Tencent Cloud TokenHub Hy3 guide](https://cloud.tencent.com/document/product/1823/132252)
- [vLLM Hy3 recipe](https://recipes.vllm.ai/tencent/Hy3)
- [SGLang Hy3 cookbook](https://lmsysorg.mintlify.app/cookbook/autoregressive/Tencent/Hy3)
