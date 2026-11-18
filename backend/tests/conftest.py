import os

# Unit tests never connect; these only satisfy settings validation.
# Integration tests run inside docker compose, where real values are already set.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("APP_ENV", "test")
