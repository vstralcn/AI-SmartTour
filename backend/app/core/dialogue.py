"""对话引擎 - LLM对话生成 + 上下文管理"""

import uuid
from collections import defaultdict
from typing import AsyncGenerator

from app.config import settings
from app.core.agent import AgentExecution, GuideAgent
from app.core.rag import rag_engine

SYSTEM_PROMPT = """你是智慧景区的AI数字人导游"小智"，性格热情开朗、知识渊博。

角色要求：
1. 回答必须基于【参考知识】中的内容，不编造信息
2. 语言亲切自然，像真人导游一样与游客交流
3. 适当加入趣味性的讲解（历史典故、民间传说等）
4. 如果参考知识中没有相关信息，坦诚告知并引导游客咨询工作人员
5. 根据游客的兴趣偏好调整讲解深度和方向
6. 使用参考知识编号标注依据，例如[1]；不得引用不存在的编号

游客兴趣：{interests}
"""


class DialogueEngine:
    """管理对话上下文和LLM调用"""

    def __init__(self):
        self.sessions: dict[str, list[dict]] = defaultdict(list)
        self.rag = rag_engine
        self.agent = GuideAgent(self.rag)

    def create_session(self, interests: list[str] | None = None) -> tuple[str, str]:
        session_id = str(uuid.uuid4())
        self.agent.create_profile(session_id, interests)
        greeting = self._generate_greeting(interests or [])
        self.sessions[session_id].append({"role": "assistant", "content": greeting})
        return session_id, greeting

    def _generate_greeting(self, interests: list[str]) -> str:
        if interests:
            interest_text = "、".join(interests)
            return (
                f"欢迎来到智慧景区！我是您的AI导游小智。"
                f"看到您对{interest_text}很感兴趣，太棒了！"
                f"我可以为您推荐最适合的游览路线，也能为您讲解景区的历史文化。"
                f"有什么想了解的，随时问我哦！"
            )
        return (
            "欢迎来到智慧景区！我是您的AI导游小智，很高兴为您服务。"
            "我可以为您介绍景区的景点、历史文化，"
            "也能根据您的兴趣推荐个性化的游览路线。有什么想问的吗？"
        )

    def prepare(self, session_id: str, user_message: str) -> AgentExecution:
        return self.agent.execute(session_id, user_message)

    async def chat(
        self,
        session_id: str,
        user_message: str,
        execution: AgentExecution,
    ) -> AsyncGenerator[str, None]:
        self.sessions[session_id].append({"role": "user", "content": user_message})

        if execution.direct_response:
            yield execution.direct_response
            self.sessions[session_id].append(
                {"role": "assistant", "content": execution.direct_response}
            )
            return

        profile = self.agent.user_profiles.get(session_id, {})
        interests = list(profile.get("interests", []))
        system_msg = SYSTEM_PROMPT.format(interests="、".join(interests) if interests else "综合")

        if execution.context:
            system_msg += f"\n\n【参考知识】\n{execution.context}"

        messages = [{"role": "system", "content": system_msg}]
        history = self.sessions[session_id][-10:]
        messages.extend(history)

        if not settings.llm_api_key:
            yield execution.grounded_answer
            self.sessions[session_id].append(
                {"role": "assistant", "content": execution.grounded_answer}
            )
            return

        full_response = ""
        async for chunk in self._call_llm_stream(messages, execution.grounded_answer):
            full_response += chunk
            yield chunk

        self.sessions[session_id].append(
            {"role": "assistant", "content": full_response}
        )

    async def _call_llm_stream(
        self,
        messages: list[dict],
        fallback_text: str,
    ) -> AsyncGenerator[str, None]:
        try:
            import openai

            client = openai.AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_api_base,
            )
            stream = await client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=1024,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception:
            yield fallback_text


dialogue_engine = DialogueEngine()
