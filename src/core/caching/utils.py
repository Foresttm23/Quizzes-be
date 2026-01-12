from __future__ import annotations

from redis.asyncio import Redis


async def delete_cache_keys(redis: Redis, *keys: str):
    if redis is None or not keys:
        return
    await redis.delete(*keys)
