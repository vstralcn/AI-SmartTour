"""语音识别服务封装 - Paraformer (FunASR)"""


async def transcribe_audio(audio_bytes: bytes, sample_rate: int = 16000) -> str:
    """将音频转换为文本

    使用Paraformer模型进行中文语音识别。
    当前为接口预留，实际部署时接入FunASR或API服务。
    """
    # TODO: 接入FunASR Paraformer模型
    # from funasr import AutoModel
    # model = AutoModel(model="paraformer-zh")
    # result = model.generate(input=audio_bytes)
    # return result[0]["text"]
    return "[语音识别结果 - 待接入ASR模型]"
