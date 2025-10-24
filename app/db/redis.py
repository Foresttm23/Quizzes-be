from redis.asyncio import Redis, ConnectionPool
from app.config import settings
from typing import Annotated
from fastapi import Depends

pool = ConnectionPool.from_url(settings.redis_url, decode_responses=True)
redis_client = Redis(connection_pool=pool)


async def get_redis_client() -> Redis:
    return redis_client


RedisDep = Annotated[Redis, Depends(get_redis_client)]
