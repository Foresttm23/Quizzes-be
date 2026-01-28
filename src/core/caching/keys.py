from __future__ import annotations

from typing import TypeVar

from fastapi import Request, Response
from fastapi_cache import FastAPICache
from pydantic import BaseModel as BaseSchema

from src.auth.models import User as UserModel

from ..dependencies import PaginationParams

SchemaType = TypeVar("SchemaType", bound=BaseSchema)


def service_key_builder(namespace: str, *args, **kwargs) -> str:
    """Services must be called with **kwargs parameters if possible. Example: quiz_service(user_id=user_id)"""
    prefix = FastAPICache.get_prefix()

    args_part = [str(arg) for arg in args]
    kwargs_part = [f"{k}:{v}" for k, v in sorted(kwargs.items())]
    key_parts = args_part + kwargs_part

    cache_key = f"{prefix}:{namespace}:{':'.join(key_parts)}"
    return cache_key


def endpoint_key_builder(
    func,
    namespace: str = "",
    request: Request = None,
    response: Response = None,
    *args,
    **kwargs,
) -> str:
    """
    Builds a specific key for caching Endpoints.
    Can extract user and pagination params for caching the endpoint.
    """
    user = kwargs.get("user") or kwargs.get("acting_user")
    user_info = f"{str(user.id)}" if isinstance(user, UserModel) else "no-user"

    pagination: PaginationParams = kwargs.get("pagination")
    pagination_info = (
        f"{pagination.page_size}:{pagination.page}"
        if isinstance(pagination, PaginationParams)
        else "no-pagination"
    )

    query_params = sorted(request.query_params.items())  # A must
    query_params_str = ":".join(f"{k}={v}" for k, v in query_params)

    return (
        f"{namespace}:{user_info}:{request.url.path}:{pagination_info}:{query_params_str}"
    )
