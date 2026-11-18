import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserSession


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_email(self, email: str) -> User | None:
        result: User | None = await self._session.scalar(select(User).where(User.email == email))
        return result

    def add_user(self, user: User) -> None:
        self._session.add(user)

    def add_session(self, user_session: UserSession) -> None:
        self._session.add(user_session)

    async def get_session_and_user(self, token_hash: str) -> tuple[UserSession, User] | None:
        row = (
            await self._session.execute(
                select(UserSession, User)
                .join(User, User.id == UserSession.user_id)
                .where(UserSession.token_hash == token_hash)
            )
        ).first()
        return (row[0], row[1]) if row else None

    async def delete_session(self, token_hash: str) -> uuid.UUID | None:
        """Delete by token hash; returns the owning user id if a session existed."""
        user_id: uuid.UUID | None = await self._session.scalar(
            delete(UserSession)
            .where(UserSession.token_hash == token_hash)
            .returning(UserSession.user_id)
        )
        return user_id

    async def delete_expired_sessions(self, now: datetime) -> None:
        await self._session.execute(delete(UserSession).where(UserSession.expires_at <= now))
