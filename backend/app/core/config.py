from functools import lru_cache
from typing import Literal

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

    @property
    def sqlalchemy_database_url(self) -> str:
        """DSN with the asyncpg driver, whatever scheme was configured."""
        url = str(self.database_url)
        scheme, rest = url.split("://", 1)
        return f"postgresql+asyncpg://{rest}" if "+" not in scheme else url


@lru_cache
def get_settings() -> Settings:
    return Settings()
