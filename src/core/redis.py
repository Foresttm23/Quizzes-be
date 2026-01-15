from typing import Any, AsyncGenerator

from redis.asyncio import ConnectionPool, Redis

from .exceptions import SessionNotInitializedException


class RedisManager:
    def __init__(self) -> None:
        self.pool: ConnectionPool | None = None

    def start(self, redis_url: str, **pool_kwargs: Any) -> None:
        if self.pool is None:
            self.pool = ConnectionPool.from_url(redis_url, **pool_kwargs)

    async def stop(self) -> None:
        if self.pool is not None:
            await self.pool.aclose()
            await self.pool.disconnect()
            self.pool = None

    async def session(self) -> AsyncGenerator[Redis, None]:
        if self.pool is None:
            raise SessionNotInitializedException(session_name="REDIS")

        client = Redis(connection_pool=self.pool)
        try:
            yield client
        finally:
            await client.close()  # Always close to return to pool


redis_manager = RedisManager()
