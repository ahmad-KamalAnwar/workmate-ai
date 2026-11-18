import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel
from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.core.db import get_database

logger = logging.getLogger(__name__)

HealthCheck = Callable[[], Awaitable[object]]

router = APIRouter(prefix="/health", tags=["health"])


class LiveResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadyResponse(BaseModel):
    status: Literal["ok", "degraded"]
    checks: dict[str, Literal["ok", "error"]]


def get_health_checks(request: Request) -> dict[str, HealthCheck]:
    redis: Redis = request.app.state.redis
    return {"database": get_database(request).ping, "redis": redis.ping}


@router.get("/live", response_model=LiveResponse)
async def live() -> LiveResponse:
    """Process is up. No dependency checks."""
    return LiveResponse()


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={503: {"model": ReadyResponse}},
)
async def ready(
    response: Response,
    checks: Annotated[dict[str, HealthCheck], Depends(get_health_checks)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReadyResponse:
    """Database and Redis reachable."""

    async def run(name: str, check: HealthCheck) -> Literal["ok", "error"]:
        try:
            await asyncio.wait_for(check(), timeout=settings.health_check_timeout_seconds)
        except Exception as exc:
            logger.warning("health check failed", extra={"check": name, "error": repr(exc)})
            return "error"
        return "ok"

    results = await asyncio.gather(*(run(n, c) for n, c in checks.items()))
    outcome = dict(zip(checks, results, strict=True))
    healthy = all(r == "ok" for r in results)
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(status="ok" if healthy else "degraded", checks=outcome)
