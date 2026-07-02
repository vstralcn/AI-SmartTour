"""LLM服务封装 - 支持Qwen/OpenAI兼容API"""

from typing import AsyncGenerator

from app.config import settings


async def chat_completion_stream(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> AsyncGenerator[str, None]:
    """流式调用LLM API"""
    import openai

    client = openai.AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_api_base,
    )

    stream = await client.chat.completions.create(
        model=model or settings.llm_model,
        messages=messages,
        stream=True,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """非流式调用LLM API"""
    import openai

    client = openai.AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_api_base,
    )

    response = await client.chat.completions.create(
        model=model or settings.llm_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content or ""
