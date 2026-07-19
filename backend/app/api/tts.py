"""语音合成 API：文本转神经语音音频。"""

from fastapi import APIRouter, HTTPException, Response

from app.models.schemas import TTSRequest
from app.services.tts import synthesize_speech

router = APIRouter()


@router.post("/tts")
async def text_to_speech(req: TTSRequest) -> Response:
    """将文本合成为音频（audio/mpeg）。

    服务端 TTS 不可用时返回 503，前端据此降级为浏览器语音。
    """
    audio = await synthesize_speech(
        text=req.text,
        voice_id=req.voice_id,
        speed=req.speed,
        pitch=req.pitch,
        emotion=req.emotion,
    )
    if not audio:
        raise HTTPException(
            status_code=503,
            detail="服务端语音合成不可用，请使用浏览器语音",
        )
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-store"},
    )
