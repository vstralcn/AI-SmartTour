"""业务持久化模型。"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ConversationSessionRecord(Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    visitor_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    interests: Mapped[list[str]] = mapped_column(JSON, default=list)
    age_group: Mapped[str] = mapped_column(String(30), default="成人")
    companions: Mapped[list[str]] = mapped_column(JSON, default=list)
    mobility: Mapped[str] = mapped_column(String(30), default="标准")
    visit_duration: Mapped[float] = mapped_column(Float, default=3.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class InteractionRecord(Base):
    __tablename__ = "interaction_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    user_message: Mapped[str] = mapped_column(Text)
    assistant_message: Mapped[str] = mapped_column(Text)
    intent: Mapped[str] = mapped_column(String(40), index=True)
    sentiment: Mapped[str] = mapped_column(String(20), index=True)
    emotion: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    response_ms: Mapped[int] = mapped_column(Integer, default=0)
    tools: Mapped[list[str]] = mapped_column(JSON, default=list)
    route_spots: Mapped[list[str]] = mapped_column(JSON, default=list)
    profile_interests: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class KnowledgeDocumentRecord(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(80), index=True)
    content: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20), default="document", index=True)
    source: Mapped[str] = mapped_column(String(200))
    file_path: Mapped[str] = mapped_column(String(500), default="")
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    upload_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )


class AvatarRecord(Base):
    __tablename__ = "avatars"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    image_url: Mapped[str] = mapped_column(String(500), default="")
    style: Mapped[str] = mapped_column(String(80), default="现代导游服")
    gender: Mapped[str] = mapped_column(String(20), default="女")
    clothing: Mapped[str] = mapped_column(String(80), default="现代导游服")
    voice_id: Mapped[str] = mapped_column(String(80), default="female-1")
    speed: Mapped[float] = mapped_column(Float, default=1.0)
    pitch: Mapped[float] = mapped_column(Float, default=1.0)
    personality: Mapped[str] = mapped_column(Text, default="")
    speaking_style: Mapped[str] = mapped_column(String(80), default="亲切自然")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
