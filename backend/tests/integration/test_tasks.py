from collections.abc import Callable
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.config import Settings
from app.core.models import utcnow
from app.tasks.models import Task, TaskStatus
from tests.integration.conftest import ClientFactory, login, run_db

pytestmark = pytest.mark.integration


def _add_tasks(settings: Settings, user: User, titles: list[str]) -> None:
    async def add(s: AsyncSession) -> None:
        now = utcnow()
        for i, title in enumerate(titles):  # later titles are newer
            s.add(Task(user_id=user.id, title=title, created_at=now + timedelta(seconds=i)))
        await s.commit()

    run_db(settings, add)


def test_tasks_require_authentication(client: TestClient) -> None:
    assert client.get("/tasks").status_code == 401


def test_lists_own_tasks_newest_first(
    client: TestClient, make_user: Callable[..., User], settings: Settings
) -> None:
    user = make_user()
    _add_tasks(settings, user, ["first", "second", "third"])
    login(client)

    response = client.get("/tasks", params={"limit": 2})

    assert response.status_code == 200
    body = response.json()
    assert [t["title"] for t in body] == ["third", "second"]
    assert body[0]["status"] == TaskStatus.PENDING
    assert body[0]["source"] == "chat"


def test_empty_list_when_no_tasks(client: TestClient, make_user: Callable[..., User]) -> None:
    make_user()
    login(client)
    assert client.get("/tasks").json() == []


def test_users_cannot_see_each_others_tasks(
    make_client: ClientFactory, make_user: Callable[..., User], settings: Settings
) -> None:
    alice = make_user(email="alice@example.com")
    make_user(email="bob@example.com")
    _add_tasks(settings, alice, ["alice's task"])

    bob = make_client()
    login(bob, email="bob@example.com")

    assert bob.get("/tasks").json() == []


@pytest.mark.parametrize("limit", [0, 101])
def test_limit_is_bounded(client: TestClient, make_user: Callable[..., User], limit: int) -> None:
    make_user()
    login(client)
    assert client.get("/tasks", params={"limit": limit}).status_code == 422
