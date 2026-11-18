from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """Owns the async engine and session factory for the app's lifetime."""

    def __init__(self, url: str) -> None:
        self.engine: AsyncEngine = create_async_engine(url, pool_pre_ping=True)
        self.sessionmaker = async_sessionmaker(self.engine, expire_on_commit=False)

    async def ping(self) -> None:
        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def dispose(self) -> None:
        await self.engine.dispose()


def get_database(request: Request) -> Database:
    db: Database = request.app.state.db
    return db


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Request-scoped session. Services own commit/rollback."""
    async with get_database(request).sessionmaker() as session:
        yield session
