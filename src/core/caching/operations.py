from __future__ import annotations

from typing import Type, TypeVar
from uuid import UUID

from fastapi_cache import FastAPICache
from pydantic import BaseModel as BaseSchema

from .serializers import deserialize

SchemaType = TypeVar("SchemaType", bound=BaseSchema)


async def set_with_mapping(mapping_key: str, key: str, value: str, expire: int):
    redis = FastAPICache.get_backend().redis

    async with redis.pipeline(transaction=True) as pipe:
        pipe.set(key, value, ex=expire)
        pipe.sadd(mapping_key, key)
        pipe.expire(mapping_key, expire)
        await pipe.execute()


async def invalidate_mapping(mapping_key: str | UUID):
    """
    Accepts the id of the mapping to invalidate.
    Example: cache_with_mapping is called with the mapping_key_name parameter, to invalidate the mapping pass this key value.
    """
    redis = FastAPICache.get_backend().redis

    keys = await redis.smembers(mapping_key)
    if keys:
        await redis.delete(*keys, mapping_key)


async def get_schema_from_cache(
    key: str, response_schema: Type[SchemaType] | None
) -> SchemaType | None:
    redis = FastAPICache.get_backend().redis
    obj = await redis.get(key)
    if not obj:
        return None
    return deserialize(obj=obj, response_schema=response_schema)
