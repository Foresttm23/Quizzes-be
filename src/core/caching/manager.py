from __future__ import annotations

import functools
from typing import Any, Callable, Type

from src.core.schemas import Base as BaseSchema
from .config import CacheConfig
from .serializers import serialize, deserialize


class CacheManager:
    """
    Usage (service instance method):

    It also exposes a decorator factory `cached` which keeps the existing
    `base_cached_service` behavior but is easier to test and mock.
    """

    def __init__(self, redis: Any | None):
        self.redis = redis

    async def _get(self, key: str, schema: Type[BaseSchema] | None = None) -> Any:
        if not self.redis:
            return None
        cached_data = await self.redis.get(key)
        if cached_data is None:
            return None
        return deserialize(obj=cached_data, schema=schema)

    async def _set(self, key: str, value: Any, expire: int | None = None) -> None:
        if not self.redis:
            return
        serialized = serialize(value)
        if expire:
            await self.redis.set(key, serialized, ex=expire)
        else:
            await self.redis.set(key, serialized)

    async def delete(self, *keys: str) -> None:
        if not self.redis or not keys:
            return
        # redis.delete accepts multiple keys
        await self.redis.delete(*keys)

    @staticmethod
    def build_key(prefix: str, *args, **kwargs) -> str:
        """Services must be called with **kwargs parameters if possible. Example: quiz_service(user_id=user_id)"""
        args_part = [str(arg) for arg in args]
        kwargs_part = [f"{k}:{v}" for k, v in sorted(kwargs.items())]

        key_parts = args_part + kwargs_part
        if not key_parts:
            key_parts = ["default"]

        cache_key = f"{prefix}:{':'.join(key_parts)}"
        return cache_key

    @staticmethod
    def cached(
            config: CacheConfig,
            schema: Type[BaseSchema] | None,
            cache_condition: Callable[[Any], bool] | None = None,
    ):
        """
        Decorator for service methods caching. Prefix for each method should be unique, expire is in seconds. Class method should have self.redis injected.
        Services must be called with **kwargs parameters if possible. Example: quiz_service(user_id=user_id).
        Schema parameter is crucial for correct serialization and deserialization.
        :cache_condition: is a function from caching rules that return a bool based on a condition.
        Example: cache_condition = lambda obj: getattr(obj, "status", None) != "IN_PROGRESS".
        """

        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(self, *args, **kwargs):
                manager: CacheManager = getattr(self, "cache_manager", None)
                if not manager:
                    return await func(self, *args, **kwargs)

                cache_key = manager.build_key(config.prefix, *args, **kwargs)

                cached = await manager._get(cache_key, schema=schema)
                if cached is not None:
                    return cached

                result = await func(self, *args, **kwargs)
                if result is None:
                    return result

                if cache_condition and not cache_condition(result):
                    return result

                await manager._set(cache_key, result, expire=config.expire)
                return result

            return wrapper

        return decorator
