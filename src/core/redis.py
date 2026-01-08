from config import settings
from redis import ConnectionPool, Redis

pool = ConnectionPool.from_url(url=str(settings.REDIS.REDIS_URL), decode_responses=True)
redis_client = Redis(connection_pool=pool)


async def get_redis_client() -> Redis:
    return redis_client
