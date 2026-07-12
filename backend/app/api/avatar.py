"""数字人形象管理API。"""

import uuid

from fastapi import APIRouter, HTTPException

from app.db.models import AvatarRecord
from app.models.schemas import AvatarConfigSchema
from app.services.persistence import (
    activate_avatar_record,
    delete_avatar_record,
    get_active_avatar_record,
    list_avatar_records,
    save_avatar_record,
)

router = APIRouter(prefix="/admin/avatar")
public_router = APIRouter(prefix="/avatar")


def _to_schema(record: AvatarRecord) -> AvatarConfigSchema:
    return AvatarConfigSchema(
        id=record.id,
        name=record.name,
        appearance={
            "image_url": record.image_url,
            "style": record.style,
        },
        voice_config={
            "voice_id": record.voice_id,
            "speed": record.speed,
            "pitch": record.pitch,
        },
        personality=record.personality,
        gender=record.gender,
        clothing=record.clothing,
        speaking_style=record.speaking_style,
        is_active=record.is_active,
    )


@router.get("/list", response_model=list[AvatarConfigSchema])
async def list_avatars():
    return [_to_schema(record) for record in await list_avatar_records()]


@public_router.get("/active", response_model=AvatarConfigSchema)
async def get_active_avatar():
    record = await get_active_avatar_record()
    if record is None:
        raise HTTPException(status_code=404, detail="暂无激活的数字人")
    return _to_schema(record)


@router.post("/config", response_model=AvatarConfigSchema)
async def save_avatar_config(config: AvatarConfigSchema):
    record = AvatarRecord(
        id=config.id or str(uuid.uuid4()),
        name=config.name,
        image_url=config.appearance.image_url,
        style=config.appearance.style,
        gender=config.gender,
        clothing=config.clothing,
        voice_id=config.voice_config.voice_id,
        speed=config.voice_config.speed,
        pitch=config.voice_config.pitch,
        personality=config.personality,
        speaking_style=config.speaking_style,
        is_active=False,
    )
    return _to_schema(await save_avatar_record(record))


@router.put("/{avatar_id}/activate")
async def activate_avatar(avatar_id: str):
    if not await activate_avatar_record(avatar_id):
        raise HTTPException(status_code=404, detail="数字人不存在")
    return {"status": "ok"}


@router.delete("/{avatar_id}")
async def delete_avatar(avatar_id: str):
    if not await delete_avatar_record(avatar_id):
        raise HTTPException(
            status_code=409,
            detail="数字人不存在或正在使用，无法删除",
        )
    return {"status": "ok"}
