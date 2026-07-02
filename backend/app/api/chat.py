"""对话交互API - WebSocket实时对话 + REST会话管理"""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.dialogue import dialogue_engine
from app.core.sentiment import analyze_digital_human_emotion
from app.models.schemas import CreateSessionRequest, CreateSessionResponse

router = APIRouter()


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(req: CreateSessionRequest):
    session_id, greeting = dialogue_engine.create_session(req.interests)
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
                user_msg = "[语音消息 - ASR转写中...]"

            emotion = analyze_digital_human_emotion(user_msg)
            await websocket.send_json(
                {"type": "emotion", "content": emotion, "done": False}
            )

            async for chunk in dialogue_engine.chat(sid, user_msg):
                await websocket.send_json(
                    {"type": "text_chunk", "content": chunk, "done": False}
                )

            await websocket.send_json(
                {"type": "text_chunk", "content": "", "done": True}
            )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json(
                {"type": "error", "content": str(e), "done": True}
            )
        except RuntimeError:
            pass
