import functools
import json
from typing import Callable

from .utils import CustomJSONEncoder


def base_cached_service(prefix: str, expire: int = 300):
    """
    Decorator for service caching. Prefix for each method should be unique, expire is in seconds. Class method should have self.redis injected.
    Services must be called with **kwargs parameters if possible. Example: quiz_service(user_id=user_id)
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            redis = getattr(self, "redis", None)
            if not redis:
                return await func(self, *args, **kwargs)

            key_parts = [str(arg) for arg in args] + [f"{k}:{v}" for k, v in kwargs.items()]
            if not key_parts:
                key_parts = ["default"]

            cache_key = f"{prefix}:{':'.join(key_parts)}"

            cached_data = await redis.get(cache_key)
            if cached_data is not None:
                return json.loads(cached_data)

            result = await func(self, *args, **kwargs)
            if result is not None:
                data = json.dumps(result, cls=CustomJSONEncoder)
                await redis.set(cache_key, data, ex=expire)

            return result

        return wrapper

    return decorator
