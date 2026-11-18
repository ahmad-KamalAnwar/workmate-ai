from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import service as audit
from app.auth.models import User, UserSession
from app.auth.rate_limit import LoginLimiter
from app.auth.repository import AuthRepository
from app.auth.security import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    hash_password,
    hash_token,
    needs_rehash,
    new_session_token,
    verify_password,
)
from app.core.config import Settings
from app.core.errors import AppError, ConflictError, InvalidCredentialsError, TooManyRequestsError
from app.core.models import utcnow

# Avoid a DB write on every request; idle expiry is accurate to this granularity.
_TOUCH_INTERVAL = timedelta(minutes=5)


def normalize_email(email: str) -> str:
    return email.strip().lower()


@dataclass(frozen=True)
class LoginResult:
    user: User
    token: str
    expires_at: datetime


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings, limiter: LoginLimiter) -> None:
        self._session = session
        self._repo = AuthRepository(session)
        self._settings = settings
        self._limiter = limiter

    async def login(
        self, email: str, password: str, *, ip: str | None, user_agent: str | None
    ) -> LoginResult:
        email = normalize_email(email)
        throttle_key = f"{ip or 'unknown'}:{email}"
        if await self._limiter.is_blocked(throttle_key):
            raise TooManyRequestsError("Too many failed login attempts. Try again later.")

        user = await self._repo.get_user_by_email(email)
        valid = verify_password(user.password_hash if user else None, password)
        if user is None or not valid or not user.is_active:
            await self._limiter.hit(throttle_key)
            audit.record(
                self._session,
                action="auth.login_failed",
                actor="user",
                user_id=user.id if user else None,
                details={"ip": ip},
            )
            await self._session.commit()
            raise InvalidCredentialsError("Invalid email or password")

        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)

        now = utcnow()
        token = new_session_token()
        expires_at = now + timedelta(minutes=self._settings.session_absolute_timeout_minutes)
        self._repo.add_session(
            UserSession(
                user_id=user.id,
                token_hash=hash_token(token),
                expires_at=expires_at,
                last_seen_at=now,
                user_agent=(user_agent or "")[:500] or None,
                ip=ip,
            )
        )
        await self._repo.delete_expired_sessions(now)
        audit.record(
            self._session, action="auth.login", actor="user", user_id=user.id, details={"ip": ip}
        )
        await self._session.commit()
        await self._limiter.reset(throttle_key)
        return LoginResult(user=user, token=token, expires_at=expires_at)

    async def authenticate(self, token: str) -> User | None:
        """Resolve a session token to an active user, enforcing idle and absolute expiry."""
        token_hash = hash_token(token)
        found = await self._repo.get_session_and_user(token_hash)
        if found is None:
            return None
        user_session, user = found
        now = utcnow()
        idle_limit = timedelta(minutes=self._settings.session_idle_timeout_minutes)
        if now >= user_session.expires_at or now - user_session.last_seen_at >= idle_limit:
            await self._repo.delete_session(token_hash)
            await self._session.commit()
            return None
        if not user.is_active:
            return None
        if now - user_session.last_seen_at >= _TOUCH_INTERVAL:
            user_session.last_seen_at = now
            await self._session.commit()
        return user

    async def logout(self, token: str) -> None:
        user_id = await self._repo.delete_session(hash_token(token))
        if user_id is not None:
            audit.record(self._session, action="auth.logout", actor="user", user_id=user_id)
        await self._session.commit()


def validate_password(password: str) -> None:
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise AppError(
            f"Password must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters long"
        )


async def create_user(
    session: AsyncSession, *, email: str, password: str, display_name: str | None = None
) -> User:
    email = normalize_email(email)
    if "@" not in email:
        raise AppError("Invalid email address")
    validate_password(password)
    repo = AuthRepository(session)
    if await repo.get_user_by_email(email) is not None:
        raise ConflictError("A user with this email already exists")
    user = User(email=email, password_hash=hash_password(password), display_name=display_name)
    repo.add_user(user)
    await session.flush()
    audit.record(session, action="auth.user_created", actor="system", user_id=user.id)
    await session.commit()
    return user
