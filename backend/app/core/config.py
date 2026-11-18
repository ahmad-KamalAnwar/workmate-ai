from functools import lru_cache
from typing import Literal

from fastapi import Request
from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables (see .env.example)."""

    model_config = SettingsConfigDict(extra="ignore", frozen=True)

    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    database_url: PostgresDsn
    redis_url: RedisDsn

    health_check_timeout_seconds: float = Field(default=2.0, gt=0, le=30)

    # Sessions
    session_cookie_name: str = "wm_session"
    session_idle_timeout_minutes: int = Field(default=60 * 24 * 7, gt=0)
    session_absolute_timeout_minutes: int = Field(default=60 * 24 * 30, gt=0)
    cookie_secure: bool = False  # must be true when served over HTTPS

    # Login throttling (per client IP + email)
    login_max_attempts: int = Field(default=10, gt=0)
    login_window_seconds: int = Field(default=15 * 60, gt=0)

    @property
    def sqlalchemy_database_url(self) -> str:
        """DSN with the asyncpg driver, whatever scheme was configured."""
        url = str(self.database_url)
        scheme, rest = url.split("://", 1)
        return f"postgresql+asyncpg://{rest}" if "+" not in scheme else url


@lru_cache
def load_settings() -> Settings:
    """Settings from the environment, for code that runs outside a request (CLI, worker)."""
    return Settings()


def get_settings(request: Request) -> Settings:
    """Request dependency: the settings the running app was created with."""
    settings: Settings = request.app.state.settings
    return settings
