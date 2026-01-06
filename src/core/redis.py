from config import settings
from core.redis import Redis, ConnectionPool

pool = ConnectionPool.from_url(settings.REDIS.REDIS_URL, decode_responses=True)
redis_client = Redis(connection_pool=pool)


async def get_redis_client() -> Redis:
    return redis_client
