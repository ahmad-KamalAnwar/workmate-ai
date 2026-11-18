import pytest
from fastapi.testclient import TestClient

from app.main import create_app

pytestmark = pytest.mark.integration


def test_ready_against_real_postgres_and_redis() -> None:
    with TestClient(create_app()) as client:  # runs lifespan: real engine and Redis client
        response = client.get("/health/ready")
    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok", "checks": {"database": "ok", "redis": "ok"}}
