"""AI-SmartTour 后端服务入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, knowledge, avatar, analytics, recommend

app = FastAPI(
    title="AI-SmartTour API",
    description="景区导览服务AI数字人 后端API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1", tags=["对话"])
app.include_router(recommend.router, prefix="/api/v1", tags=["推荐"])
app.include_router(knowledge.router, prefix="/api/v1", tags=["知识库"])
app.include_router(avatar.router, prefix="/api/v1", tags=["数字人"])
app.include_router(analytics.router, prefix="/api/v1", tags=["数据分析"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ai-smarttour"}
