import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        ("postgresql://u:p@db:5432/app", "postgresql+asyncpg://u:p@db:5432/app"),
        ("postgresql+asyncpg://u:p@db:5432/app", "postgresql+asyncpg://u:p@db:5432/app"),
    ],
)
def test_sqlalchemy_url_uses_asyncpg(configured: str, expected: str) -> None:
    settings = Settings(database_url=configured, redis_url="redis://r:6379/0")
    assert settings.sqlalchemy_database_url == expected


def test_invalid_database_url_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="not-a-url", redis_url="redis://r:6379/0")


def test_invalid_log_level_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql://u:p@db/app",
            redis_url="redis://r:6379/0",
            log_level="LOUD",
        )
