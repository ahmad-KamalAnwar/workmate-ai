import uuid
from typing import Any, Literal

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, CreatedAt, UUIDPrimaryKey

Actor = Literal["user", "agent", "system"]


class AuditLog(UUIDPrimaryKey, CreatedAt, Base):
    """Append-only record of security-relevant and external actions."""

    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_log_user_id_created_at", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    actor: Mapped[str] = mapped_column(String(16))
    action: Mapped[str] = mapped_column(String(100))
    target: Mapped[str | None] = mapped_column(String(300))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
