import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import Actor, AuditLog


def record(
    session: AsyncSession,
    *,
    action: str,
    actor: Actor,
    user_id: uuid.UUID | None = None,
    target: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Add an audit entry to the caller's transaction (committed with the unit of work).

    Never put secrets, tokens, or passwords in `details`.
    """
    session.add(
        AuditLog(user_id=user_id, actor=actor, action=action, target=target, details=details or {})
    )
