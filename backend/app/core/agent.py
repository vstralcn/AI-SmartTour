"""轻量导览 Agent：意图识别、画像更新和受控工具调用。"""

import re
import uuid
from dataclasses import dataclass, field

from app.core.rag import KnowledgeEvidence, RAGEngine
from app.core.recommend import recommend_route

INTEREST_LABELS = (
    "历史文化",
    "自然风光",
    "民俗体验",
    "美食探索",
    "摄影打卡",
    "亲子游玩",
)

INTEREST_ALIASES = {
    "历史": "历史文化",
    "古建筑": "历史文化",
    "文化": "历史文化",
    "自然": "自然风光",
    "园林": "自然风光",
    "风景": "自然风光",
    "民俗": "民俗体验",
    "非遗": "民俗体验",
    "美食": "美食探索",
    "吃": "美食探索",
    "摄影": "摄影打卡",
    "拍照": "摄影打卡",
    "亲子": "亲子游玩",
    "孩子": "亲子游玩",
    "儿童": "亲子游玩",
}


@dataclass(frozen=True)
class AgentStep:
    tool: str
    status: str
    detail: str


@dataclass
class AgentExecution:
    intent: str
    steps: list[AgentStep] = field(default_factory=list)
    evidence: list[KnowledgeEvidence] = field(default_factory=list)
    context: str = ""
    grounded_answer: str = ""
    direct_response: str = ""
    confidence: float = 0.0


class GuideAgent:
    """使用白名单工具完成导览任务，不允许模型直接执行外部操作。"""

    def __init__(self, rag: RAGEngine):
        self.rag = rag
        self.user_profiles: dict[str, dict[str, object]] = {}
        self.feedback_records: list[dict[str, str]] = []

    def create_profile(self, session_id: str, interests: list[str] | None = None) -> None:
        self.user_profiles[session_id] = {
            "interests": list(dict.fromkeys(interests or [])),
            "visit_duration": 3.0,
        }

    def execute(self, session_id: str, message: str) -> AgentExecution:
        profile = self.user_profiles.setdefault(
            session_id,
            {"interests": [], "visit_duration": 3.0},
        )
        profile_step = self._update_profile(profile, message)
        intent = self._classify_intent(message)

        if intent == "route_planning":
            execution = self._plan_route(profile, message)
        elif intent == "feedback":
            execution = self._record_feedback(session_id, message)
        else:
            execution = self._query_knowledge(message)

        if profile_step:
            execution.steps.insert(0, profile_step)
        return execution

    @staticmethod
    def capabilities() -> list[dict[str, str]]:
        return [
            {"name": "knowledge", "description": "检索景区知识并返回来源与置信度"},
            {"name": "route", "description": "根据时长和兴趣生成可解释路线"},
            {"name": "profile", "description": "从对话中更新匿名游客兴趣画像"},
            {"name": "feedback", "description": "记录游客建议或投诉并生成编号"},
        ]

    def _update_profile(self, profile: dict[str, object], message: str) -> AgentStep | None:
        current = list(profile.get("interests", []))
        detected = [label for label in INTEREST_LABELS if label in message]
        detected.extend(
            label
            for keyword, label in INTEREST_ALIASES.items()
            if keyword in message
        )
        merged = list(dict.fromkeys([*current, *detected]))
        if merged == current:
            return None

        profile["interests"] = merged
        return AgentStep(
            tool="profile",
            status="completed",
            detail=f"已更新兴趣画像：{'、'.join(merged)}",
        )

    @staticmethod
    def _classify_intent(message: str) -> str:
        if any(keyword in message for keyword in ("公交", "地铁", "自驾", "怎么去", "交通")):
            return "knowledge_query"
        if any(keyword in message for keyword in ("路线", "行程", "怎么游", "先去", "游玩")):
            return "route_planning"
        if any(keyword in message for keyword in ("投诉", "建议", "不满意", "反馈")):
            return "feedback"
        return "knowledge_query"

    def _plan_route(self, profile: dict[str, object], message: str) -> AgentExecution:
        duration = self._extract_duration(message)
        if duration is None:
            duration = float(profile.get("visit_duration", 3.0))
        else:
            profile["visit_duration"] = duration

        interests = list(profile.get("interests", []))
        route, description = recommend_route(duration_hours=duration, interests=interests)
        route_lines = [
            f"{index}. {spot['name']}（约 {spot['recommended_duration']} 分钟）"
            for index, spot in enumerate(route, start=1)
        ]
        response = "\n".join(
            [
                description,
                "",
                *route_lines,
                "",
                f"规划依据：游览时长 {duration:g} 小时"
                + (f"，兴趣偏好 {'、'.join(interests)}" if interests else "，综合游览"),
            ]
        )
        return AgentExecution(
            intent="route_planning",
            steps=[
                AgentStep(
                    tool="route",
                    status="completed",
                    detail=f"已按 {duration:g} 小时和 {len(interests)} 个兴趣标签规划路线",
                )
            ],
            direct_response=response,
            confidence=1.0,
        )

    def _query_knowledge(self, message: str) -> AgentExecution:
        result = self.rag.retrieve_with_sources(message)
        if not result.found:
            return AgentExecution(
                intent="knowledge_query",
                steps=[
                    AgentStep(
                        tool="knowledge",
                        status="no_result",
                        detail="景区知识库中没有找到足够相关的证据",
                    )
                ],
                direct_response=(
                    "抱歉，当前景区知识库中没有足够依据回答这个问题。"
                    "您可以换一种问法，或请景区工作人员确认。"
                ),
                confidence=0.0,
            )

        context_parts = [
            f"[{index}] {item.title}\n{item.content}"
            for index, item in enumerate(result.evidence, start=1)
        ]
        return AgentExecution(
            intent="knowledge_query",
            steps=[
                AgentStep(
                    tool="knowledge",
                    status="completed",
                    detail=(
                        f"通过 {result.matched_by} 检索到 {len(result.evidence)} 条证据，"
                        f"置信度 {result.confidence:.0%}"
                    ),
                )
            ],
            evidence=result.evidence,
            context="\n\n".join(context_parts),
            grounded_answer=result.answer,
            confidence=result.confidence,
        )

    def _record_feedback(self, session_id: str, message: str) -> AgentExecution:
        feedback_id = f"FB-{uuid.uuid4().hex[:8].upper()}"
        self.feedback_records.append(
            {"id": feedback_id, "session_id": session_id, "content": message}
        )
        return AgentExecution(
            intent="feedback",
            steps=[
                AgentStep(
                    tool="feedback",
                    status="completed",
                    detail=f"反馈已记录，编号 {feedback_id}",
                )
            ],
            direct_response=(
                f"感谢您的反馈，已记录到当前服务实例，编号 {feedback_id}。"
                "正式部署时可将该工具对接景区工单系统。"
            ),
            confidence=1.0,
        )

    @staticmethod
    def _extract_duration(message: str) -> float | None:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:个)?小时", message)
        if not match:
            return None
        duration = float(match.group(1))
        return min(max(duration, 0.5), 12.0)
