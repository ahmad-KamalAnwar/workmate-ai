"""Integration fixtures: a dedicated `<db>_test` database migrated with Alembic, Redis db 1.

Run inside docker compose: `docker compose exec api pytest -m integration`.
"""

import asyncio
from collections.abc import Awaitable, Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from redis import Redis as SyncRedis
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command
from app.auth.models import User
from app.auth.service import create_user
from app.core.config import Settings, load_settings
from app.core.csrf import CSRF_HEADER, CSRF_VALUE
from app.core.db import Database
from app.main import create_app

BACKEND_ROOT = Path(__file__).resolve().parents[2]
TABLES = ("tasks", "sessions", "audit_log", "users")
PASSWORD = "correct horse battery staple"


def _alembic_config(url: str) -> Config:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    cfg.attributes["database_url"] = url
    cfg.attributes["configure_logger"] = False
    return cfg


async def _recreate_database(admin_url: str, name: str) -> None:
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        await conn.execute(text(f'CREATE DATABASE "{name}"'))
    await engine.dispose()


@pytest.fixture(scope="session")
def settings() -> Settings:
    base = load_settings()
    url = make_url(base.sqlalchemy_database_url)
    test_db = f"{url.database}_test"
    asyncio.run(_recreate_database(url.set(database="postgres").render_as_string(False), test_db))
    test_url = url.set(database=test_db).render_as_string(hide_password=False)

    # Exercise the migrations both ways before using the schema.
    cfg = _alembic_config(test_url)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")

    redis_url = str(base.redis_url).rsplit("/", 1)[0] + "/1"  # db 1 is reserved for tests
    return base.model_copy(
        update={"database_url": test_url, "redis_url": redis_url, "app_env": "test"}
    )


def run_db[T](settings: Settings, fn: Callable[[AsyncSession], Awaitable[T]]) -> T:
    """Run `fn` with a fresh session outside the app (for setup and assertions)."""

    async def go() -> T:
        db = Database(settings.sqlalchemy_database_url)
        try:
            async with db.sessionmaker() as session:
                return await fn(session)
        finally:
            await db.dispose()

    return asyncio.run(go())


@pytest.fixture(autouse=True)
def _clean_state(settings: Settings) -> Iterator[None]:
    yield

    async def truncate(session: AsyncSession) -> None:
        await session.execute(text(f"TRUNCATE {', '.join(TABLES)} CASCADE"))
        await session.commit()

    run_db(settings, truncate)
    with SyncRedis.from_url(str(settings.redis_url)) as redis:
        redis.flushdb()


ClientFactory = Callable[..., TestClient]


@pytest.fixture
def make_client(settings: Settings) -> Iterator[ClientFactory]:
    """Clients run the real app lifespan (engine + Redis). Override settings via kwargs."""
    clients: list[TestClient] = []

    def make(**overrides: Any) -> TestClient:
        client = TestClient(create_app(settings.model_copy(update=overrides)))
        client.headers[CSRF_HEADER] = CSRF_VALUE
        client.__enter__()
        clients.append(client)
        return client

    yield make
    for client in clients:
        client.__exit__(None, None, None)


@pytest.fixture
def client(make_client: ClientFactory) -> TestClient:
    return make_client()


@pytest.fixture
def make_user(settings: Settings) -> Callable[..., User]:
    def make(email: str = "user@example.com", password: str = PASSWORD) -> User:
        return run_db(settings, lambda s: create_user(s, email=email, password=password))

    return make


def login(client: TestClient, email: str = "user@example.com", password: str = PASSWORD) -> Any:
    return client.post("/auth/login", json={"email": email, "password": password})
