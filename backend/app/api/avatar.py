"""数字人形象管理API"""

import uuid

from fastapi import APIRouter

from app.models.schemas import AvatarConfigSchema

router = APIRouter(prefix="/admin/avatar")

_avatars: list[AvatarConfigSchema] = [
    AvatarConfigSchema(
        id="1",
        name="小智",
        appearance={"image_url": "/avatars/xiaozhi.png", "style": "现代"},
        voice_config={"voice_id": "female-1", "speed": 1.0, "pitch": 1.0},
        personality="热情开朗，善于讲故事，知识渊博",
        is_active=True,
    ),
    AvatarConfigSchema(
        id="2",
        name="文渊",
        appearance={"image_url": "/avatars/wenyuan.png", "style": "古典汉服"},
        voice_config={"voice_id": "male-1", "speed": 0.9, "pitch": 0.95},
        personality="博学稳重，擅长历史文化讲解",
        is_active=False,
    ),
]


@router.get("/list", response_model=list[AvatarConfigSchema])
async def list_avatars():
    return _avatars


@router.post("/config", response_model=AvatarConfigSchema)
async def save_avatar_config(config: AvatarConfigSchema):
    existing = next((a for a in _avatars if a.id == config.id), None)
    if existing:
        idx = _avatars.index(existing)
        _avatars[idx] = config
        return config

    config.id = str(uuid.uuid4())
    _avatars.append(config)
    return config


@router.put("/{avatar_id}/activate")
async def activate_avatar(avatar_id: str):
    for a in _avatars:
        a.is_active = a.id == avatar_id
    return {"status": "ok"}
