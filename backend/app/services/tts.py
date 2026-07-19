"""语音合成服务封装

优先使用 edge-tts（微软 Neural 音色，免费、无需 GPU、自然度高），
未安装或调用失败时返回空字节，由前端降级为浏览器 SpeechSynthesis。

情绪 / 语速 / 音高会映射为韵律参数（rate/pitch），让讲解有轻重缓急，
降低机械感。CosyVoice 等本地引擎可在此处按同一接口替换接入。
"""

import logging

logger = logging.getLogger(__name__)

# voice_id -> edge-tts 中文 Neural 音色
_VOICE_MAP = {
    "female-1": "zh-CN-XiaoxiaoNeural",
    "female-2": "zh-CN-XiaoyiNeural",
    "male-1": "zh-CN-YunxiNeural",
    "male-2": "zh-CN-YunjianNeural",
}
_DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"

# 情绪 -> (语速增量 %, 音高增量 Hz)：面对老人放慢、投诉更关切、讲解沉稳
_EMOTION_PROSODY = {
    "happy": (5, 4),
    "excited": (10, 6),
    "caring": (-8, -3),
    "explaining": (-4, 0),
    "neutral": (0, 0),
}


def _resolve_voice(voice_id: str) -> str:
    return _VOICE_MAP.get(voice_id, _DEFAULT_VOICE)


def _build_prosody(speed: float, pitch: float, emotion: str) -> tuple[str, str]:
    """把角色音色参数与情绪叠加为 edge-tts 的 rate / pitch 字符串。"""
    emo_rate, emo_pitch = _EMOTION_PROSODY.get(emotion, (0, 0))
    rate_pct = round((speed - 1.0) * 100) + emo_rate
    pitch_hz = round((pitch - 1.0) * 50) + emo_pitch
    rate_pct = max(-40, min(40, rate_pct))
    pitch_hz = max(-20, min(20, pitch_hz))
    return f"{rate_pct:+d}%", f"{pitch_hz:+d}Hz"


async def synthesize_speech(
    text: str,
    voice_id: str = "female-1",
    speed: float = 1.0,
    pitch: float = 1.0,
    emotion: str = "neutral",
) -> bytes:
    """将文本合成为 MP3 音频字节。

    返回空字节表示服务端 TTS 不可用（未安装依赖或网络失败），
    调用方应据此降级到浏览器语音，保证链路不中断。
    """
    text = (text or "").strip()
    if not text:
        return b""

    try:
        import edge_tts
    except ImportError:
        logger.warning("edge-tts 未安装，跳过服务端 TTS（前端将降级为浏览器语音）")
        return b""

    voice = _resolve_voice(voice_id)
    rate, pitch_str = _build_prosody(speed, pitch, emotion)

    try:
        communicate = edge_tts.Communicate(
            text, voice, rate=rate, pitch=pitch_str)
        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
        return bytes(audio)
    except Exception:
        logger.exception("edge-tts 合成失败，返回空音频以触发前端降级")
        return b""
