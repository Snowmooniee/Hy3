# Hy3 API 快速开始

[English](./quickstart.md) | 简体中文

本指南将帮助你完成第一次 Hy3 API 调用，并了解其核心 API 功能。如果你已经拥有 TokenHub API 密钥或正在运行的自托管端点，应当能在 5 分钟内获得首次响应。

## 选择 API 访问方式

设置客户端前，请先选择一种 API 访问方式：

| 访问方式 | 适用场景 | 开始前所需准备 |
| --- | --- | --- |
| TokenHub | 无需在本地部署模型即可调用 Hy3 | 已开通 TokenHub 的腾讯云账号、获准访问 Hy3 的 API 密钥，以及服务所在地域的基础 URL |
| 自托管 API | 你或你的组织已经通过 vLLM 或 SGLang 运行 Hy3 | 正在运行的 OpenAI 兼容端点及其服务端提供的模型名称 |

本指南假设 TokenHub 服务或自托管端点已经可用。账号开通、模型下载和服务器部署不计入 5 分钟首次调用流程。

有关自托管部署的说明，请参阅[推理和部署](./README_CN.md#推理和部署)。

## 设置客户端环境

请在仓库根目录创建专用虚拟环境。如果已有其他虚拟环境处于激活状态，请先退出，再继续。

### Linux 和 macOS

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

这些命令只安装 API 示例所需的客户端依赖，不会下载 Hy3 模型权重，也不会启动推理服务。

## 配置 API 连接

示例通过环境变量读取连接配置。这样既可以避免凭据进入源代码，也能让同一组示例连接 TokenHub 或自托管服务器。

### 环境变量

| 变量 | 说明 |
| --- | --- |
| `HY3_PROVIDER` | 选择提供方对应的请求格式：`tokenhub`、`vllm` 或 `sglang` |
| `HY3_BASE_URL` | OpenAI 兼容 API 的基础 URL，包含 `/v1` |
| `HY3_API_KEY` | TokenHub API 密钥；对于未启用身份验证的自托管服务器，填写 `EMPTY` |
| `HY3_MODEL` | API 请求使用的模型名称；自托管服务应填写服务端实际提供的模型名称 |

使用 TokenHub 广州地域时，请在当前终端会话中设置以下变量：

```bash
export HY3_PROVIDER="tokenhub"
export HY3_BASE_URL="https://tokenhub.tencentmaas.com/v1"
export HY3_API_KEY="YOUR_API_KEY"
export HY3_MODEL="hy3"
```

在 Windows PowerShell 中：

```powershell
$env:HY3_PROVIDER="tokenhub"
$env:HY3_BASE_URL="https://tokenhub.tencentmaas.com/v1"
$env:HY3_API_KEY="YOUR_API_KEY"
$env:HY3_MODEL="hy3"
```

请只在本地替换 `YOUR_API_KEY`。切勿将真实 API 密钥写入此文件或示例脚本，也不要将其包含在对外分享的终端输出或 Git 提交中。

TokenHub 新加坡地域用户应使用 `https://tokenhub-intl.tencentmaas.com/v1`。自托管用户应根据下文的兼容性矩阵选择相应的连接配置。

## 发送第一个请求

下面的基础请求有意不使用任何提供方特定的推理选项，因此可作为 TokenHub、vLLM 和 SGLang 的共同起点。

### curl

以下命令使用 Bash 语法。Windows PowerShell 用户可以使用后面的 Python 示例。

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

## 解析响应

OpenAI 兼容的聊天补全响应会返回一个 `choices` 列表。对于基础请求，读取其中第一个选项：

| 字段 | 含义 |
| --- | --- |
| `choice.message.content` | 助手生成的文本 |
| `choice.finish_reason` | 生成停止的原因，例如 `stop` 或 `length` |
| `response.usage` | 提供方返回的 token 用量信息 |

部分兼容端点可能不返回 `usage` 字段，因此 Python 示例会先检查该字段是否存在，再读取 token 数量。推理内容、流式响应分块和工具调用需要采用不同的解析方式，具体请参阅相应示例。

## 常用参数

| 参数 | 作用 | Hy3 建议 |
| --- | --- | --- |
| `temperature` | 控制采样随机性 | 建议从本仓库推荐的 `0.9` 开始 |
| `top_p` | 控制核采样范围 | 建议从本仓库推荐的 `1.0` 开始 |
| `max_tokens` | 限制本次请求生成的 token 数量 | 根据任务需求和所选端点施加的限制设置合适的值 |
| `stop` | 遇到指定字符串或字符串列表中的任一项时停止生成 | 仅在应用程序有明确停止序列时设置 |
| `tools` | 提供模型可以请求调用的 OpenAI 兼容函数定义 | 应用程序必须校验并执行模型选择的函数；自托管服务器还需配置文档指定的工具调用解析器 |
| `stream` | 返回增量聊天补全分块，而不是等待完整响应 | 适用于交互式应用；应逐个解析分块，再组装最终响应 |

支持的取值、默认值和限制可能因提供方及服务配置而异。本指南仅对 `temperature` 和 `top_p` 使用仓库推荐值，不假设其他字段存在适用于所有端点的仓库级默认值。

推理字段因提供方而异，请使用下方与所选提供方匹配的请求结构。

## 提供方兼容性

连接配置：

| 提供方 | `HY3_PROVIDER` | 基础 URL | API 密钥 | 模型 |
| --- | --- | --- | --- | --- |
| TokenHub（广州） | `tokenhub` | `https://tokenhub.tencentmaas.com/v1` | 必填 | `hy3` |
| TokenHub（新加坡） | `tokenhub` | `https://tokenhub-intl.tencentmaas.com/v1` | 必填 | `hy3` |
| vLLM（使用本仓库的部署命令） | `vllm` | `http://127.0.0.1:8000/v1` | `EMPTY`，除非部署时已配置身份验证 | `hy3` |
| SGLang（使用本仓库的部署命令） | `sglang` | `http://127.0.0.1:8000/v1` | `EMPTY`，除非部署时已配置身份验证 | `hy3` |

### 推理模式

Hy3 支持三种推理强度：`no_think` 用于直接响应，`low` 用于降低推理强度，`high` 用于对复杂任务进行更深入的推理。本仓库使用的自托管聊天模板默认采用 `no_think`。托管服务的默认值可能不同，因此应显式设置所需模式。

请只选择下列一种 Python SDK 请求结构：

| 提供方 | Python SDK `extra_body` | 运行高级示例所需的服务器配置 |
| --- | --- | --- |
| TokenHub | `{"reasoning_effort": effort}` | 由 TokenHub 托管 |
| vLLM | `{"chat_template_kwargs": {"reasoning_effort": effort}}` | 使用 `--reasoning-parser hy_v3`；工具调用还需要 `--tool-call-parser hy_v3` 和 `--enable-auto-tool-choice`。启用推理的工具调用循环还需要在 `chat_template_kwargs` 中设置 `interleaved_thinking=true` |
| SGLang | `{"reasoning_effort": effort}` | 使用本仓库部署命令时，配置 `--reasoning-parser hunyuan` 和 `--tool-call-parser hunyuan` |

将 `effort` 替换为 `no_think`、`low` 或 `high`。对于 TokenHub 和 SGLang，`extra_body` 会将 `reasoning_effort` 添加到 JSON 请求的顶层；对于 vLLM，该字段仍嵌套在 `chat_template_kwargs` 中。

在启用推理的工具调用循环中，应先完整保留助手消息的 `content`、`reasoning_content` 和 `tool_calls`，再追加每条 `role=tool` 的执行结果。

不要同时使用顶层形式和嵌套形式。只使用与所选提供方对应的请求结构。

## 速率限制

本仓库未定义固定的每分钟请求数或每分钟 token 数限制。TokenHub 的限制会因账号、套餐、模型服务、地域和平台策略而异；自托管服务的限制则取决于硬件、服务器配置、并发量以及端点前方的网关。

当 API 返回 HTTP `429` 时，应降低请求速率，并在响应包含 `Retry-After` 时遵循该字段。关于不依赖仓库级固定限制的有上限重试处理，请参阅[重试示例](./examples/api/error_handling_retry.py)。

## 运行示例

示例脚本使用上文配置的同一组 `HY3_PROVIDER`、`HY3_BASE_URL`、`HY3_API_KEY` 和 `HY3_MODEL` 环境变量。

首先在仓库根目录运行基础聊天示例：

```bash
python examples/api/basic_chat.py
```

有关可用示例、预期行为和不同提供方的注意事项，请参阅 [API 示例指南](./examples/api/README.md)。

## 故障排查

| 现象 | 排查内容 |
| --- | --- |
| 缺少环境变量或出现 Python `KeyError` | 确认当前终端会话中已经设置全部四个 `HY3_*` 环境变量 |
| 连接错误或超时 | 确认端点可以访问；使用自托管服务时，确认服务器正在运行 |
| HTTP `400` | 检查请求字段，并确认推理或工具配置与所选提供方匹配 |
| HTTP `401` 或 `403` | 检查 API 密钥、账号权限、地域和端点；凭据未改变时不要重试 |
| HTTP `404` 或模型不存在错误 | 确认基础 URL 包含 `/v1`，并确认 `HY3_MODEL` 与服务端提供的模型名称一致 |
| HTTP `429` | 降低请求速率，并在响应包含 `Retry-After` 时遵循该字段 |
| 可恢复的 HTTP `5xx` | 使用有上限的退避策略重试，不要无限重试 |

只重试超时、连接失败、HTTP `429` 和可恢复的 `5xx` 响应。HTTP `400`、`401` 和 `403` 属于请求或配置错误，应立即失败，不进行重试。

## 延伸阅读

- [Hy3 推理和部署说明](./README_CN.md#推理和部署)
- [Hy3 API 示例](./examples/api/README.md)
- [腾讯云 TokenHub Hy3 指南](https://cloud.tencent.com/document/product/1823/132252)
- [vLLM Hy3 使用指南](https://recipes.vllm.ai/tencent/Hy3)
- [SGLang Hy3 使用指南](https://lmsysorg.mintlify.app/cookbook/autoregressive/Tencent/Hy3)
