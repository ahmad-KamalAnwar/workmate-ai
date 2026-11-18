import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.core.db import get_session
from app.tasks.models import TaskSource, TaskStatus
from app.tasks.repository import TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source: TaskSource
    status: TaskStatus
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


def get_task_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> TaskRepository:
    return TaskRepository(session)


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    user: CurrentUser,
    repo: Annotated[TaskRepository, Depends(get_task_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[TaskOut]:
    """Most recent tasks for the current user."""
    return [TaskOut.model_validate(t) for t in await repo.list_recent(user.id, limit)]
