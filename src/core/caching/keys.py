from __future__ import annotations

from typing import TypeVar

from fastapi_cache import FastAPICache
from pydantic import BaseModel as BaseSchema

SchemaType = TypeVar("SchemaType", bound=BaseSchema)


def custom_key_builder(namespace: str, *args, **kwargs) -> str:
    """Services must be called with **kwargs parameters if possible. Example: quiz_service(user_id=user_id)"""
    prefix = FastAPICache.get_prefix()

    args_part = [str(arg) for arg in args]
    kwargs_part = [f"{k}:{v}" for k, v in sorted(kwargs.items())]
    key_parts = args_part + kwargs_part

    cache_key = f"{prefix}:{namespace}:{':'.join(key_parts)}"
    return cache_key
