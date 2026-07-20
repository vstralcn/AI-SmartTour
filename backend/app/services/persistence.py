"""核心业务数据持久化。"""

from datetime import datetime

from sqlalchemy import delete, select, update

from app.core.rag import rag_engine
from app.db import session_scope
from app.db.models import (
    AvatarRecord,
    ConversationSessionRecord,
    InteractionRecord,
    KnowledgeDocumentRecord,
)


async def seed_defaults() -> None:
    async with session_scope() as session:
        avatar_count = len((await session.scalars(select(AvatarRecord.id))).all())
        if avatar_count == 0:
            session.add_all(
                [
                    AvatarRecord(
                        id="xiaozhi",
                        name="小智",
                        image_url="/avatars/xiaozhi.png",
                        style="现代国风",
                        gender="女",
                        clothing="现代导游服",
                        voice_id="female-1",
                        speed=1.0,
                        pitch=1.05,
                        personality="热情开朗，善于讲故事，知识渊博",
                        speaking_style="亲切活泼",
                        is_active=True,
                    ),
                    AvatarRecord(
                        id="wenyuan",
                        name="文渊",
                        image_url="/avatars/wenyuan.png",
                        style="古典汉服",
                        gender="男",
                        clothing="传统汉服",
                        voice_id="male-1",
                        speed=0.9,
                        pitch=0.95,
                        personality="博学稳重，擅长历史文化讲解",
                        speaking_style="沉稳叙事",
                        is_active=False,
                    ),
                ]
            )

        knowledge_count = len(
            (await session.scalars(select(KnowledgeDocumentRecord.id))).all()
        )
        if knowledge_count == 0:
            for entry in rag_engine.export_entries():
                session.add(
                    KnowledgeDocumentRecord(
                        id=str(entry["id"]),
                        title=str(entry["title"]),
                        category=str(entry["category"]),
                        content=str(entry["content"]),
                        kind=str(entry["kind"]),
                        source=str(entry["source"]),
                        keywords=list(entry["keywords"]),
                        tags=list(entry["tags"]),
                        status="active",
                    )
                )
        await session.commit()

    await sync_rag_from_database()


async def sync_rag_from_database() -> None:
    records = await list_knowledge_records(active_only=True)
    rag_engine.replace_entries(
        [
            {
                "id": record.id,
                "title": record.title,
                "category": record.category,
                "content": record.content,
                "kind": record.kind,
                "source": record.source,
                "keywords": record.keywords,
                "tags": record.tags,
                "status": record.status,
            }
            for record in records
        ]
    )


async def save_conversation_session(
    session_id: str,
    visitor_id: str | None,
    interests: list[str],
    age_group: str,
    companions: list[str],
    mobility: str,
    visit_duration: float,
) -> None:
    async with session_scope() as session:
        session.add(
            ConversationSessionRecord(
                id=session_id,
                visitor_id=visitor_id,
                interests=interests,
                age_group=age_group,
                companions=companions,
                mobility=mobility,
                visit_duration=visit_duration,
            )
        )
        await session.commit()


async def save_interaction(
    session_id: str,
    user_message: str,
    assistant_message: str,
    intent: str,
    sentiment: str,
    emotion: str,
    confidence: float,
    response_ms: int,
    tools: list[str],
    route_spots: list[str],
    profile_interests: list[str],
) -> None:
    async with session_scope() as session:
        session.add(
            InteractionRecord(
                session_id=session_id,
                user_message=user_message,
                assistant_message=assistant_message,
                intent=intent,
                sentiment=sentiment,
                emotion=emotion,
                confidence=confidence,
                response_ms=response_ms,
                tools=tools,
                route_spots=route_spots,
                profile_interests=profile_interests,
            )
        )
        await session.commit()


async def list_knowledge_records(
    active_only: bool = False,
) -> list[KnowledgeDocumentRecord]:
    statement = select(KnowledgeDocumentRecord).order_by(
        KnowledgeDocumentRecord.updated_at.desc()
    )
    if active_only:
        statement = statement.where(KnowledgeDocumentRecord.status == "active")
    async with session_scope() as session:
        return list((await session.scalars(statement)).all())


async def get_knowledge_record(doc_id: str) -> KnowledgeDocumentRecord | None:
    async with session_scope() as session:
        return await session.get(KnowledgeDocumentRecord, doc_id)


async def save_knowledge_record(
    record: KnowledgeDocumentRecord,
) -> KnowledgeDocumentRecord:
    async with session_scope() as session:
        existing = await session.get(KnowledgeDocumentRecord, record.id)
        if existing is None:
            session.add(record)
        else:
            existing.title = record.title
            existing.category = record.category
            existing.content = record.content
            existing.kind = record.kind
            existing.source = record.source
            existing.file_path = record.file_path
            existing.keywords = record.keywords
            existing.tags = record.tags
            existing.status = record.status
            existing.updated_at = datetime.now()
            record = existing
        await session.commit()
        await session.refresh(record)
    await sync_rag_from_database()
    return record


async def delete_knowledge_record(doc_id: str) -> bool:
    async with session_scope() as session:
        result = await session.execute(
            delete(KnowledgeDocumentRecord).where(
                KnowledgeDocumentRecord.id == doc_id
            )
        )
        await session.commit()
    await sync_rag_from_database()
    return result.rowcount > 0


async def list_avatar_records() -> list[AvatarRecord]:
    async with session_scope() as session:
        statement = select(AvatarRecord).order_by(
            AvatarRecord.is_active.desc(),
            AvatarRecord.created_at.asc(),
        )
        return list((await session.scalars(statement)).all())


async def get_active_avatar_record() -> AvatarRecord | None:
    async with session_scope() as session:
        statement = select(AvatarRecord).where(AvatarRecord.is_active.is_(True))
        return (await session.scalars(statement)).first()


async def conversation_session_exists(session_id: str) -> bool:
    """确认游客会话存在，避免把签名服务暴露成无门槛额度消耗接口。"""
    async with session_scope() as session:
        statement = select(ConversationSessionRecord.id).where(
            ConversationSessionRecord.id == session_id
        )
        return (await session.scalar(statement)) is not None


async def save_avatar_record(record: AvatarRecord) -> AvatarRecord:
    async with session_scope() as session:
        existing = await session.get(AvatarRecord, record.id)
        if existing is None:
            session.add(record)
        else:
            existing.name = record.name
            existing.image_url = record.image_url
            existing.style = record.style
            existing.gender = record.gender
            existing.clothing = record.clothing
            existing.voice_id = record.voice_id
            existing.speed = record.speed
            existing.pitch = record.pitch
            existing.personality = record.personality
            existing.speaking_style = record.speaking_style
            existing.updated_at = datetime.now()
            record = existing
        await session.commit()
        await session.refresh(record)
        return record


async def activate_avatar_record(avatar_id: str) -> bool:
    async with session_scope() as session:
        record = await session.get(AvatarRecord, avatar_id)
        if record is None:
            return False
        await session.execute(update(AvatarRecord).values(is_active=False))
        record.is_active = True
        record.updated_at = datetime.now()
        await session.commit()
        return True


async def delete_avatar_record(avatar_id: str) -> bool:
    async with session_scope() as session:
        record = await session.get(AvatarRecord, avatar_id)
        if record is None or record.is_active:
            return False
        await session.delete(record)
        await session.commit()
        return True


async def database_is_ready() -> bool:
    try:
        async with session_scope() as session:
            await session.execute(select(ConversationSessionRecord.id).limit(1))
        return True
    except Exception:
        return False
