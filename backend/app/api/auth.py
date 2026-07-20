"""管理员登录 API。"""

from collections import defaultdict, deque
from time import monotonic

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.core.auth import admin_auth_configured, authenticate_admin, create_admin_token
from app.models.schemas import AdminLoginRequest, AdminLoginResponse

router = APIRouter(prefix="/auth/admin")

_LOGIN_WINDOW_SECONDS = 300.0
_LOGIN_MAX_ATTEMPTS = 10
_login_attempts: defaultdict[str, deque[float]] = defaultdict(deque)


def _allow_login_attempt(client_id: str) -> bool:
    now = monotonic()
    attempts = _login_attempts[client_id]
    while attempts and now - attempts[0] >= _LOGIN_WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= _LOGIN_MAX_ATTEMPTS:
        return False
    attempts.append(now)
    return True


@router.post("/login", response_model=AdminLoginResponse)
async def login_admin(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
) -> AdminLoginResponse:
    response.headers["Cache-Control"] = "no-store"
    if not admin_auth_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="管理员认证尚未配置",
            headers={"Cache-Control": "no-store"},
        )

    client_id = request.client.host if request.client else "unknown"
    if not _allow_login_attempt(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="登录尝试过于频繁，请稍后再试",
            headers={"Cache-Control": "no-store", "Retry-After": "300"},
        )
    if not authenticate_admin(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"Cache-Control": "no-store"},
        )

    token, expires_at = create_admin_token()
    return AdminLoginResponse(access_token=token, expires_at=expires_at)
