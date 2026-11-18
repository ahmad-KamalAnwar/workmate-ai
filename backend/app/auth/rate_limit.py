from typing import Protocol

from redis.asyncio import Redis


class LoginLimiter(Protocol):
    async def is_blocked(self, key: str) -> bool: ...
    async def hit(self, key: str) -> None: ...
    async def reset(self, key: str) -> None: ...


class RedisLoginLimiter:
    """Fixed-window failure counter: block after `max_attempts` failures per window."""

    def __init__(self, redis: Redis, *, max_attempts: int, window_seconds: int) -> None:
        self._redis = redis
        self._max = max_attempts
        self._window = window_seconds

    @staticmethod
    def _key(key: str) -> str:
        return f"login-failures:{key}"

    async def is_blocked(self, key: str) -> bool:
        count = await self._redis.get(self._key(key))
        return count is not None and int(count) >= self._max

    async def hit(self, key: str) -> None:
        k = self._key(key)
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.incr(k)
            pipe.expire(k, self._window, nx=True)
            await pipe.execute()

    async def reset(self, key: str) -> None:
        await self._redis.delete(self._key(key))
