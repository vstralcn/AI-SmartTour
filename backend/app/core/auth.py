"""管理员认证：环境凭据登录 + HMAC 短期访问令牌。"""

import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

_bearer = HTTPBearer(auto_error=False)


def admin_auth_configured() -> bool:
    return bool(
        settings.admin_username.strip()
        and settings.admin_password
        and len(settings.admin_token_secret) >= 32
    )


def authenticate_admin(username: str, password: str) -> bool:
    if not admin_auth_configured():
        return False
    return hmac.compare_digest(username, settings.admin_username) and hmac.compare_digest(
        password, settings.admin_password
    )


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_admin_token() -> tuple[str, int]:
    now = int(time.time())
    ttl_minutes = max(1, min(settings.admin_token_ttl_minutes, 1440))
    expires_at = now + ttl_minutes * 60
    payload = json.dumps(
        {
            "sub": settings.admin_username,
            "iat": now,
            "exp": expires_at,
            "nonce": secrets.token_hex(8),
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    encoded_payload = _base64url_encode(payload)
    signature = hmac.new(
        settings.admin_token_secret.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{encoded_payload}.{_base64url_encode(signature)}", expires_at


def verify_admin_token(token: str) -> dict[str, object] | None:
    if not admin_auth_configured():
        return None
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        expected = hmac.new(
            settings.admin_token_secret.encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()
        supplied = _base64url_decode(encoded_signature)
        if not hmac.compare_digest(expected, supplied):
            return None
        payload = json.loads(_base64url_decode(encoded_payload))
        if not isinstance(payload, dict):
            return None
        if payload.get("sub") != settings.admin_username:
            return None
        if int(payload.get("exp", 0)) <= int(time.time()):
            return None
        return payload
    except (ValueError, TypeError, json.JSONDecodeError, binascii.Error):
        return None


async def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict[str, object]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    payload = verify_admin_token(credentials.credentials)
    if payload is None:
        raise _unauthorized()
    return payload


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="管理员登录已失效，请重新登录",
        headers={"WWW-Authenticate": "Bearer", "Cache-Control": "no-store"},
    )
