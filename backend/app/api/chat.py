"""对话交互API - WebSocket实时对话 + REST会话管理"""

import json
import logging
from time import perf_counter

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.dialogue import dialogue_engine
from app.core.sentiment import analyze_digital_human_emotion, analyze_emotion
from app.models.schemas import CreateSessionRequest, CreateSessionResponse
from app.services.persistence import (
    get_active_avatar_record,
    save_conversation_session,
    save_interaction,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/agent/capabilities")
async def agent_capabilities():
    return {"mode": "single-orchestrator", "tools": dialogue_engine.agent.capabilities()}


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(req: CreateSessionRequest):
    avatar = await get_active_avatar_record()
    session_id, greeting = dialogue_engine.create_session(
        interests=req.interests,
        age_group=req.age_group,
        companions=req.companions,
        mobility=req.mobility,
        visit_duration=req.visit_duration,
        guide_name=avatar.name if avatar else "小智",
        guide_personality=(
            avatar.personality if avatar else "热情开朗，知识渊博"
        ),
        speaking_style=avatar.speaking_style if avatar else "亲切自然",
    )
    await save_conversation_session(
        session_id=session_id,
        visitor_id=req.visitor_id,
        interests=req.interests,
        age_group=req.age_group,
        companions=req.companions,
        mobility=req.mobility,
        visit_duration=req.visit_duration,
    )
    return CreateSessionResponse(session_id=session_id, greeting=greeting)


@router.websocket("/chat/stream")
async def chat_stream(websocket: WebSocket):
    await websocket.accept()
    session_id = websocket.query_params.get("session_id", "")

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            user_msg = data.get("content", "")
            msg_type = data.get("type", "text")
            sid = data.get("session_id", session_id)

            if msg_type == "audio":
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": (
                            "服务端 Paraformer 尚未配置。"
                            "请使用游客端浏览器实时语音识别，或改用文字输入。"
                        ),
                        "done": True,
                    }
                )
                continue

            started_at = perf_counter()
            sentiment = analyze_emotion(user_msg)
            emotion = analyze_digital_human_emotion(user_msg)
            await websocket.send_json(
                {"type": "emotion", "content": emotion, "done": False}
            )

            execution = dialogue_engine.prepare(sid, user_msg)
            for step in execution.steps:
                await websocket.send_json(
                    {
                        "type": "agent_step",
                        "content": {
                            "tool": step.tool,
                            "status": step.status,
                            "detail": step.detail,
                        },
                        "done": False,
                    }
                )

            if execution.evidence:
                await websocket.send_json(
                    {
                        "type": "sources",
                        "content": [
                            {
                                "title": item.title,
                                "category": item.category,
                                "score": item.score,
                                "source": item.source,
                            }
                            for item in execution.evidence
                        ],
                        "done": False,
                    }
                )

            full_response = ""
            async for chunk in dialogue_engine.chat(sid, user_msg, execution):
                full_response += chunk
                await websocket.send_json(
                    {"type": "text_chunk", "content": chunk, "done": False}
                )

            await websocket.send_json(
                {"type": "text_chunk", "content": "", "done": True}
            )
            profile = dialogue_engine.agent.user_profiles.get(sid, {})
            try:
                await save_interaction(
                    session_id=sid,
                    user_message=user_msg,
                    assistant_message=full_response,
                    intent=execution.intent,
                    sentiment=sentiment,
                    emotion=emotion,
                    confidence=execution.confidence,
                    response_ms=round((perf_counter() - started_at) * 1000),
                    tools=[step.tool for step in execution.steps],
                    route_spots=execution.route_spots,
                    profile_interests=list(profile.get("interests", [])),
                )
            except Exception:
                logger.exception("Failed to persist interaction event")

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json(
                {"type": "error", "content": str(e), "done": True}
            )
        except RuntimeError:
            pass
