"""数字人推理服务 - MuseTalk口型驱动

当前为占位服务，实际部署时接入MuseTalk模型。
启用方式: docker compose --profile gpu up -d
"""

from fastapi import FastAPI

app = FastAPI(title="Digital Human Service", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "digital-human", "engine": "musetalk"}


@app.post("/generate")
async def generate():
    return {"status": "placeholder", "message": "MuseTalk推理服务待接入"}
