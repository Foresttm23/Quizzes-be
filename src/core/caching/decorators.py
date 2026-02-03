import functools
from typing import Any, Callable, Type

from pydantic import BaseModel as BaseSchema

from ..exceptions import CacheKeyNotExistException
from .config import CacheConfig
from .keys import service_key_builder
from .operations import get_schema_from_cache, set_with_mapping
from .serializers import serialize


def cache_with_mapping[S: BaseSchema](
    *,
    config: CacheConfig,
    response_schema: Type[S] | None,
    cache_condition: Callable[[Any], bool] | None = None,
) -> Callable[[Any], Any] | S:
    """
    Custom decorator that caches result and adds the key to a Shadow Set.
    Services must be called with **kwargs parameters if possible. Example: quiz_service(user_id=user_id).

    mapping_key_name: The name of the kwarg to use as the ID.
    Example: mapping_key_name="quiz_id".

    response_schema: Always pass the "advanced" schema (Admin) and sanitize it later.
    Schema parameter is crucial for correct serialization and deserialization.

    :cache_condition: is a function from caching rules that return a bool based on a condition.
    Example: cache_condition = lambda obj: getattr(obj, "status", None) != "IN_PROGRESS".
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            mapping_id = str(kwargs.get(config.mapping_key_name))
            mapping_key = config.get_mapping_key(mapping_id)
            if not mapping_key:
                raise CacheKeyNotExistException(mapping=mapping_id)

            cache_key = service_key_builder(namespace=func.__name__, *args, **kwargs)

            cached = await get_schema_from_cache(
                key=cache_key, response_schema=response_schema
            )
            if cached:
                return cached

            result = await func(self, *args, **kwargs)
            if result is None:
                return result

            if cache_condition and not cache_condition(result):
                return result

            await set_with_mapping(
                mapping_key=mapping_key,
                key=cache_key,
                value=serialize(result),
                expire=config.expire,
            )

            return result

        return wrapper

    return decorator
