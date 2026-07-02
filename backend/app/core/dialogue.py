"""对话引擎 - LLM对话生成 + 上下文管理"""

import uuid
from collections import defaultdict
from typing import AsyncGenerator

from app.config import settings
from app.core.rag import RAGEngine

SYSTEM_PROMPT = """你是智慧景区的AI数字人导游"小智"，性格热情开朗、知识渊博。

角色要求：
1. 回答必须基于【参考知识】中的内容，不编造信息
2. 语言亲切自然，像真人导游一样与游客交流
3. 适当加入趣味性的讲解（历史典故、民间传说等）
4. 如果参考知识中没有相关信息，坦诚告知并引导游客咨询工作人员
5. 根据游客的兴趣偏好调整讲解深度和方向

游客兴趣：{interests}
"""


class DialogueEngine:
    """管理对话上下文和LLM调用"""

    def __init__(self):
        self.sessions: dict[str, list[dict]] = defaultdict(list)
        self.user_profiles: dict[str, dict] = {}
        self.rag = RAGEngine()

    def create_session(self, interests: list[str] | None = None) -> tuple[str, str]:
        session_id = str(uuid.uuid4())
        self.user_profiles[session_id] = {"interests": interests or []}
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

    async def chat(
        self, session_id: str, user_message: str
    ) -> AsyncGenerator[str, None]:
        self.sessions[session_id].append({"role": "user", "content": user_message})

        context = self.rag.retrieve(user_message)

        interests = self.user_profiles.get(session_id, {}).get("interests", [])
        system_msg = SYSTEM_PROMPT.format(interests="、".join(interests) if interests else "综合")

        if context:
            system_msg += f"\n\n【参考知识】\n{context}"

        messages = [{"role": "system", "content": system_msg}]
        history = self.sessions[session_id][-10:]
        messages.extend(history)

        full_response = ""
        async for chunk in self._call_llm_stream(messages):
            full_response += chunk
            yield chunk

        self.sessions[session_id].append(
            {"role": "assistant", "content": full_response}
        )

    async def _call_llm_stream(
        self, messages: list[dict]
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
            yield self._fallback_response(messages[-1]["content"])

    def _fallback_response(self, user_msg: str) -> str:
        responses = {
            "历史": "这里有着深厚的历史底蕴。据史料记载，早在唐代就已经是著名的游览胜地。"
            "历代文人墨客在此留下了大量诗词佳作，是了解中国传统文化的绝佳去处。",
            "美食": "说到美食，这里可是美食天堂！推荐您一定要尝尝本地特色小吃，"
            "还有传统手工制作的糕点。景区内的餐厅是最受游客欢迎的用餐地点。",
            "路线": "根据您的兴趣，我推荐以下路线：先参观入口处的历史展览馆（约30分钟），"
            "然后沿着古道前行至主景区（约1小时），最后到达观景台欣赏全景。全程约3小时。",
            "门票": "景区门票价格为成人80元/人，学生及60岁以上老人可享半价优惠。"
            "开放时间为每日8:00-18:00。",
            "时间": "景区开放时间为每日8:00-18:00，建议上午入园，可以充分游览。"
            "旺季（5-10月）建议提前网上预约购票。",
        }
        for key, val in responses.items():
            if key in user_msg:
                return val
        return (
            "这是一个很好的问题！这个景区有着丰富的历史文化底蕴，"
            "您可以在这里感受到传统与现代的完美融合。"
            "如果您想了解更详细的信息，可以告诉我您最感兴趣的方面。"
        )


dialogue_engine = DialogueEngine()
