"""LLM服务封装 - 支持Qwen/OpenAI兼容API"""

from typing import AsyncGenerator

from app.config import settings

# 事实问答使用低温度，降低编造风险（README：低温度事实问答）
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 1024
# 调用超时（秒）：避免上游卡住拖垮首字响应 P95
DEFAULT_TIMEOUT = 30.0


def _create_client(timeout: float = DEFAULT_TIMEOUT):
    """创建 OpenAI 兼容异步客户端。"""
    import openai

    return openai.AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_api_base,
        timeout=timeout,
    )


async def chat_completion_stream(
    messages: list[dict],
    model: str | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: float = DEFAULT_TIMEOUT,
) -> AsyncGenerator[str, None]:
    """流式调用LLM API"""
    client = _create_client(timeout)
    stream = await client.chat.completions.create(
        model=model or settings.llm_model,
        messages=messages,
        stream=True,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: float = DEFAULT_TIMEOUT,
) -> str:
    """非流式调用LLM API"""
    client = _create_client(timeout)
    response = await client.chat.completions.create(
        model=model or settings.llm_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )

    return response.choices[0].message.content or ""
