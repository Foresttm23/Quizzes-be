from __future__ import annotations

import functools
import json
from typing import Any, Callable, Type

from redis.asyncio import Redis

from src.core.schemas import Base as BaseSchema

from .constants import CacheConfig


def base_cached_service(config: CacheConfig, schema: Type[BaseSchema] | None, cache_condition: Callable[[Any], bool] | None = None):
    """
    Decorator for service methods caching. Prefix for each method should be unique, expire is in seconds. Class method should have self.redis injected.
    Services must be called with **kwargs parameters if possible. Example: quiz_service(user_id=user_id).
    Schema parameter is crucial for correct serialization and desirialization.
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
                return _deserialize(obj=cached_data, schema=schema)

            result = await func(*args, **kwargs)
            if result is None:
                return result

            if cache_condition and not cache_condition(result):
                return result

            serialized_data = _serialize(result)
            await redis.set(cache_key, serialized_data, ex=config.expire)

            return result

        return wrapper

    return decorator


async def delete_cache_keys(redis: Redis, *keys: str):
    if redis is None or not keys:
        return
    await redis.delete(*keys)


def _serialize(obj: Any) -> str:
    """
    Serializes Pydantic models, Lists of models, or raw dicts.
    Handles UUIDs and Datetimes automatically.
    """
    if isinstance(obj, BaseSchema):
        return obj.model_dump_json()

    if isinstance(obj, list):
        data_list = [item.model_dump(mode="json") if isinstance(item, BaseSchema) else item for item in obj]
        return json.dumps(data_list, default=str)

    return json.dumps(obj, default=str)


def _deserialize(obj: Any, schema: Type[BaseSchema] | None) -> Any:
    """Deserialize obg into a passed schema."""
    json_data = json.loads(obj)  # Only schemas here, no plain dict or list
    if schema is None:
        return json_data

    if isinstance(json_data, list):
        return [schema.model_validate(item) for item in json_data]
    return schema.model_validate(json_data)


def build_cache_key(prefix: str, *args, **kwargs) -> str:
    """Services must be called with **kwargs parameters if possible. Example: quiz_service(user_id=user_id)"""
    args_part = [str(arg) for arg in args]
    kwargs_part = [f"{k}:{v}" for k, v in sorted(kwargs.items())]

    key_parts = args_part + kwargs_part
    if not key_parts:
        key_parts = ["default"]

    cache_key = f"{prefix}:{':'.join(key_parts)}"
    return cache_key
