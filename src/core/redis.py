from redis import ConnectionPool, Redis

from config import settings

pool = ConnectionPool.from_url(settings.REDIS.REDIS_URL, decode_responses=True)
redis_client = Redis(connection_pool=pool)


async def get_redis_client() -> Redis:
    return redis_client
