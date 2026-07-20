"""数字人形象管理API。"""

import base64
import hashlib
import hmac
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from urllib.parse import urlparse
from wsgiref.handlers import format_date_time

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.config import settings
from app.core.auth import require_admin
from app.db.models import AvatarRecord
from app.models.schemas import AvatarConfigSchema
from app.services.persistence import (
    activate_avatar_record,
    conversation_session_exists,
    delete_avatar_record,
    get_active_avatar_record,
    list_avatar_records,
    save_avatar_record,
)

router = APIRouter(prefix="/admin/avatar", dependencies=[Depends(require_admin)])
public_router = APIRouter(prefix="/avatar")

_SIGNED_URL_WINDOW_SECONDS = 60.0
_SIGNED_URL_MAX_REQUESTS = 10
_signed_url_requests: defaultdict[str, deque[float]] = defaultdict(deque)


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


def _build_signed_url(server_url: str, api_key: str, api_secret: str) -> str:
    """按讯飞开放平台握手鉴权生成带签名的 wss 地址。

    apiSecret 仅在后端参与 HMAC-SHA256 签名，不会随响应下发前端。
    apiKey 会作为 authorization 的 Base64 内容传给讯飞，因此不能视为隐藏字段。
    """
    parsed = urlparse(server_url)
    host = parsed.netloc
    path = parsed.path or "/v1/interact"
    # RFC1123 格式的 GMT 时间
    date = format_date_time(datetime.now(timezone.utc).timestamp())
    signature_origin = (
        f"host: {host}\n"
        f"date: {date}\n"
        f"GET {path} HTTP/1.1"
    )
    signature_sha = hmac.new(
        api_secret.encode("utf-8"),
        signature_origin.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    signature = base64.b64encode(signature_sha).decode("utf-8")
    authorization_origin = (
        f'api_key="{api_key}", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature}"'
    )
    authorization = base64.b64encode(
        authorization_origin.encode("utf-8")
    ).decode("utf-8")
    # 与讯飞 SDK 内部拼接方式逐字节一致：authorization/date/host 原样拼接，
    # 不做 URL 编码。服务端按原始串校验签名，多一层百分号编码会导致 11203。
    query = f"authorization={authorization}&date={date}&host={host}"
    return f"{server_url}?{query}"


def _check_signed_url_rate(session_id: str) -> bool:
    now = time.monotonic()
    requests = _signed_url_requests[session_id]
    while requests and now - requests[0] >= _SIGNED_URL_WINDOW_SECONDS:
        requests.popleft()
    if len(requests) >= _SIGNED_URL_MAX_REQUESTS:
        return False
    requests.append(now)
    return True


@public_router.get("/xunfei/signed-url")
async def get_xunfei_signed_url(
    response: Response,
    session_id: str | None = Query(default=None, min_length=1, max_length=80),
):
    """下发讯飞虚拟人 Web SDK 接入所需的非敏感参数与签名地址。

    六项配置齐全时返回 enabled=true 与 signedUrl（不含 apiSecret 明文）；
    缺任何一项返回 enabled=false，前端据此降级回 VRM。
    """
    response.headers["Cache-Control"] = "no-store"
    required = [
        settings.xf_avatar_app_id,
        settings.xf_avatar_api_key,
        settings.xf_avatar_api_secret,
        settings.xf_avatar_scene_id,
        settings.xf_avatar_avatar_id,
        settings.xf_avatar_vcn,
    ]
    if not all(value.strip() for value in required):
        return {"enabled": False}

    if not session_id or not await conversation_session_exists(session_id):
        raise HTTPException(
            status_code=401,
            detail="无效的游客会话",
            headers={"Cache-Control": "no-store"},
        )
    if not _check_signed_url_rate(session_id):
        raise HTTPException(
            status_code=429,
            detail="讯飞连接请求过于频繁，请稍后再试",
            headers={"Cache-Control": "no-store", "Retry-After": "60"},
        )

    signed_url = _build_signed_url(
        settings.xf_avatar_server_url,
        settings.xf_avatar_api_key,
        settings.xf_avatar_api_secret,
    )
    return {
        "enabled": True,
        "appId": settings.xf_avatar_app_id,
        "sceneId": settings.xf_avatar_scene_id,
        "avatarId": settings.xf_avatar_avatar_id,
        "vcn": settings.xf_avatar_vcn,
        "signedUrl": signed_url,
    }
