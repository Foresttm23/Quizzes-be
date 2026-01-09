from typing import Any

from redis.asyncio import ConnectionPool

redis_pool: ConnectionPool | None = None


def init_redis(redis_url: str, pool_kwargs: dict[str, Any] | None = None):
    global redis_pool
    redis_pool = ConnectionPool.from_url(redis_url, **(pool_kwargs or {}))
    return redis_pool
