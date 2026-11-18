import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, CreatedAt, UUIDPrimaryKey


class TaskStatus(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskSource(StrEnum):
    CHAT = "chat"
    SCHEDULE = "schedule"


class Task(UUIDPrimaryKey, CreatedAt, Base):
    """Minimal task record; steps, plans, and conversation links arrive in Phases 2-3."""

    __tablename__ = "tasks"
    __table_args__ = (Index("ix_tasks_user_id_created_at", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(300))
    source: Mapped[str] = mapped_column(String(16), default=TaskSource.CHAT)
    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.PENDING)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]
