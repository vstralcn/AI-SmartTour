"""异步数据库会话与初始化。"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, pool_pre_ping=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)
_initialization_lock = asyncio.Lock()
_initialized = False


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session


async def init_database() -> None:
    global _initialized
    if _initialized:
        return

    from app.db import models  # noqa: F401

    async with _initialization_lock:
        if _initialized:
            return
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        _initialized = True


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    await init_database()
    async with async_session() as session:
        yield session
