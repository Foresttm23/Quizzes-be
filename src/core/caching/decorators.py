from __future__ import annotations

import functools
from typing import Any, Callable, Type

from src.core.schemas import Base as BaseSchema
from .config import CacheConfig
from .keys import build_cache_key
from .seriallizers import serialize, deserialize


def base_cached_service(config: CacheConfig, schema: Type[BaseSchema] | None, cache_condition: Callable[[Any], bool] | None = None):
    """
    Decorator for service methods caching. Prefix for each method should be unique, expire is in seconds. Class method should have self.redis injected.
    Services must be called with **kwargs parameters if possible. Example: quiz_service(user_id=user_id).
    Schema parameter is crucial for correct serialization and deserialization.
    :cache_condition: is a function from caching rules that return a bool based on a condition.
    Example: cache_condition = lambda: getattr(obj, "status", None) != "IN_PROGRESS".
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            self_instance = args[0]
            redis = getattr(self_instance, "redis", None)
            if not redis:
                return await func(*args, **kwargs)

            cache_key = build_cache_key(prefix=config.prefix, *args[1:], **kwargs)

            cached_data = await redis.get(cache_key)
            if cached_data is not None:
                return deserialize(obj=cached_data, schema=schema)

            result = await func(*args, **kwargs)
            if result is None:
                return result

            if cache_condition and not cache_condition(result):
                return result

            serialized_data = serialize(result)
            await redis.set(cache_key, serialized_data, ex=config.expire)

            return result

        return wrapper

    return decorator





