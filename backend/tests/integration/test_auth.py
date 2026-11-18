from collections.abc import Callable
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.auth.models import User, UserSession
from app.auth.service import create_user
from app.core.config import Settings
from app.core.errors import AppError, ConflictError
from app.core.models import utcnow
from tests.integration.conftest import PASSWORD, ClientFactory, login, run_db

pytestmark = pytest.mark.integration


def _audit_actions(settings: Settings) -> list[str]:
    async def q(s: AsyncSession) -> list[str]:
        return list(await s.scalars(select(AuditLog.action).order_by(AuditLog.created_at)))

    return run_db(settings, q)


def _session_count(settings: Settings) -> int:
    async def q(s: AsyncSession) -> int:
        return int(await s.scalar(select(func.count()).select_from(UserSession)) or 0)

    return run_db(settings, q)


def test_login_sets_secure_cookie_and_me_returns_user(
    client: TestClient, make_user: Callable[..., User], settings: Settings
) -> None:
    make_user(email="User@Example.com")  # stored lower-cased

    response = login(client, email="  USER@example.com ")

    assert response.status_code == 200, response.text
    assert response.json()["email"] == "user@example.com"
    assert response.json()["timezone"] == "Asia/Karachi"
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{settings.session_cookie_name}=")
    assert "HttpOnly" in cookie
    assert "samesite=lax" in cookie.lower()
    assert "password" not in response.text

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"
    assert _audit_actions(settings) == ["auth.user_created", "auth.login"]


@pytest.mark.parametrize(
    ("email", "password"),
    [("user@example.com", "wrong password!"), ("nobody@example.com", PASSWORD)],
)
def test_bad_credentials_return_same_generic_error(
    client: TestClient, make_user: Callable[..., User], email: str, password: str
) -> None:
    make_user()
    response = login(client, email=email, password=password)
    assert response.status_code == 401
    assert response.json() == {
        "error": {"code": "invalid_credentials", "message": "Invalid email or password"}
    }
    assert "set-cookie" not in response.headers


def test_failed_login_is_audited(
    client: TestClient, make_user: Callable[..., User], settings: Settings
) -> None:
    make_user()
    login(client, password="wrong password!")
    assert _audit_actions(settings)[-1] == "auth.login_failed"


def test_login_is_throttled_after_repeated_failures(
    make_client: ClientFactory, make_user: Callable[..., User]
) -> None:
    make_user()
    client = make_client(login_max_attempts=3)
    for _ in range(3):
        assert login(client, password="wrong password!").status_code == 401

    blocked = login(client)  # even the correct password is refused while blocked
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "too_many_requests"


def test_successful_login_resets_failure_count(
    make_client: ClientFactory, make_user: Callable[..., User]
) -> None:
    make_user()
    client = make_client(login_max_attempts=3)
    for _ in range(2):
        login(client, password="wrong password!")
    assert login(client).status_code == 200
    for _ in range(2):
        login(client, password="wrong password!")
    assert login(client).status_code == 200


def test_state_changing_request_without_csrf_header_is_rejected(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user()
    del client.headers["X-Requested-With"]
    response = login(client)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_failed"


def test_logout_revokes_session(
    client: TestClient, make_user: Callable[..., User], settings: Settings
) -> None:
    make_user()
    login(client)
    assert _session_count(settings) == 1

    response = client.post("/auth/logout")

    assert response.status_code == 204
    assert _session_count(settings) == 0
    assert client.get("/auth/me").status_code == 401
    assert _audit_actions(settings)[-1] == "auth.logout"


def test_logout_without_session_is_harmless(client: TestClient) -> None:
    assert client.post("/auth/logout").status_code == 204


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_forged_cookie_is_rejected(client: TestClient, settings: Settings) -> None:
    client.cookies.set(settings.session_cookie_name, "not-a-real-token")
    assert client.get("/auth/me").status_code == 401


@pytest.mark.parametrize("field", ["expires_at", "last_seen_at"])
def test_expired_or_idle_session_is_rejected_and_deleted(
    client: TestClient, make_user: Callable[..., User], settings: Settings, field: str
) -> None:
    make_user()
    login(client)
    past = utcnow() - timedelta(days=60)

    async def expire(s: AsyncSession) -> None:
        await s.execute(update(UserSession).values({field: past}))
        await s.commit()

    run_db(settings, expire)

    assert client.get("/auth/me").status_code == 401
    assert _session_count(settings) == 0


def test_inactive_user_cannot_log_in(
    client: TestClient, make_user: Callable[..., User], settings: Settings
) -> None:
    make_user()

    async def deactivate(s: AsyncSession) -> None:
        await s.execute(update(User).values(is_active=False))
        await s.commit()

    run_db(settings, deactivate)
    assert login(client).status_code == 401


def test_validation_errors_use_the_error_envelope(client: TestClient) -> None:
    response = client.post("/auth/login", json={"email": "a@b.c"})
    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "validation_error"
    assert body["details"][0]["loc"] == ["body", "password"]


def test_create_user_rejects_duplicates_and_weak_passwords(
    make_user: Callable[..., User], settings: Settings
) -> None:
    make_user()
    with pytest.raises(ConflictError):
        run_db(settings, lambda s: create_user(s, email="USER@example.com", password=PASSWORD))
    with pytest.raises(AppError, match="Password must be"):
        run_db(settings, lambda s: create_user(s, email="new@example.com", password="short"))
