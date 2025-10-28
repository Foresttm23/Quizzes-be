from redis.asyncio import Redis, ConnectionPool

from app.core.config import settings

pool = ConnectionPool.from_url(settings.redis.redis_url, decode_responses=True)
redis_client = Redis(connection_pool=pool)


async def get_redis_client() -> Redis:
    return redis_client
