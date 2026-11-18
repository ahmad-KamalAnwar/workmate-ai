from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.auth.rate_limit import LoginLimiter, RedisLoginLimiter
from app.auth.service import AuthService
from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.core.errors import NotAuthenticatedError
from app.core.redis import get_redis


def get_login_limiter(
    redis: Annotated[Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginLimiter:
    return RedisLoginLimiter(
        redis,
        max_attempts=settings.login_max_attempts,
        window_seconds=settings.login_window_seconds,
    )


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    limiter: Annotated[LoginLimiter, Depends(get_login_limiter)],
) -> AuthService:
    return AuthService(session, settings, limiter)


async def get_current_user(
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    token = request.cookies.get(settings.session_cookie_name)
    user = await service.authenticate(token) if token else None
    if user is None:
        raise NotAuthenticatedError("Not authenticated")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
