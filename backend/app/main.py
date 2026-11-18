from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.db import Database
from app.core.logging import configure_logging
from app.health.router import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.db = Database(settings.sqlalchemy_database_url)
    app.state.redis = Redis.from_url(str(settings.redis_url))
    try:
        yield
    finally:
        await app.state.redis.aclose()
        await app.state.db.dispose()


def create_app() -> FastAPI:
    configure_logging(get_settings().log_level)
    app = FastAPI(title="WorkMate AI", version="0.1.0", lifespan=lifespan)
    app.include_router(health_router)
    return app


app = create_app()
