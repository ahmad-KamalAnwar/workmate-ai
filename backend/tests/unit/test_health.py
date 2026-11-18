import asyncio
from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.health.router import HealthCheck, get_health_checks
from app.main import create_app


async def _ok() -> None:
    return None


async def _fail() -> None:
    raise ConnectionError("down")


async def _hang() -> None:
    await asyncio.sleep(10)


ClientFactory = Callable[[dict[str, HealthCheck]], TestClient]


@pytest.fixture
def client_with() -> Iterator[ClientFactory]:
    """Build a client whose health checks are replaced with fakes (no lifespan, no I/O)."""
    app = create_app()

    def make(checks: dict[str, HealthCheck]) -> TestClient:
        app.dependency_overrides[get_health_checks] = lambda: checks
        app.dependency_overrides[get_settings] = lambda: Settings(
            database_url="postgresql://u:p@db/app",
            redis_url="redis://r:6379/0",
            health_check_timeout_seconds=0.05,
        )
        return TestClient(app)

    yield make
    app.dependency_overrides.clear()


def test_live_needs_no_dependencies() -> None:
    response = TestClient(create_app()).get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_ok_when_all_checks_pass(client_with: ClientFactory) -> None:
    response = client_with({"database": _ok, "redis": _ok}).get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "ok", "redis": "ok"}}


def test_ready_503_when_a_check_fails(client_with: ClientFactory) -> None:
    response = client_with({"database": _ok, "redis": _fail}).get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "checks": {"database": "ok", "redis": "error"},
    }


def test_ready_503_when_a_check_times_out(client_with: ClientFactory) -> None:
    response = client_with({"database": _hang, "redis": _ok}).get("/health/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "error"
