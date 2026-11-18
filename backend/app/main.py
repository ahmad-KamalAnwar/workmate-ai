from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from app.auth.router import router as auth_router
from app.core.config import Settings, load_settings
from app.core.csrf import CSRFHeaderMiddleware
from app.core.db import Database
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.health.router import router as health_router
from app.tasks.router import router as tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    app.state.db = Database(settings.sqlalchemy_database_url)
    app.state.redis = Redis.from_url(str(settings.redis_url))
    try:
        yield
    finally:
        await app.state.redis.aclose()
        await app.state.db.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="WorkMate AI", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(CSRFHeaderMiddleware)
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(tasks_router)
    return app


app = create_app()
