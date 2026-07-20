"""AI-SmartTour 后端服务入口"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, auth, avatar, chat, digital_human_broadcast, knowledge, recommend, tts
from app.config import settings
from app.core.dialogue import dialogue_engine
from app.db import init_database
from app.services.persistence import database_is_ready, seed_defaults


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await init_database()
    await seed_defaults()
    yield

app = FastAPI(
    title="AI-SmartTour API",
    description="景区导览服务AI数字人 后端API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1", tags=["对话"])
app.include_router(auth.router, prefix="/api/v1", tags=["管理员认证"])
app.include_router(recommend.router, prefix="/api/v1", tags=["推荐"])
app.include_router(knowledge.router, prefix="/api/v1", tags=["知识库"])
app.include_router(avatar.router, prefix="/api/v1", tags=["数字人"])
app.include_router(avatar.public_router, prefix="/api/v1", tags=["数字人"])
app.include_router(analytics.router, prefix="/api/v1", tags=["数据分析"])
app.include_router(digital_human_broadcast.router,
                   prefix="/api/v1", tags=["数字人播报"])
app.include_router(tts.router, prefix="/api/v1", tags=["语音合成"])


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "ai-smarttour",
        "agent_mode": "single-orchestrator",
        "knowledge_documents": len(dialogue_engine.rag.knowledge_base),
        "database": "ready" if await database_is_ready() else "unavailable",
    }
