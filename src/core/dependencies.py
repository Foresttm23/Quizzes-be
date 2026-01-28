from dataclasses import dataclass, fields
from typing import Annotated, AsyncGenerator

from fastapi import Depends, Query
from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import db_session_manager
from .http_client import http_client_manager
from .redis import redis_manager


@dataclass
class PaginationParams:
    page: int = Query(default=1, ge=1, description="Page number")
    page_size: int = Query(
        default=10,
        ge=1,
        le=settings.APP.MAX_PAGE_SIZE,
        description="Number of items per page",
    )

    @classmethod
    def get_fields_repr(cls) -> set[str]:
        return {f.name for f in fields(cls)}


PaginationParamDep = Annotated[PaginationParams, Depends()]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Exception is handled inside the postgres_module.sessionmanager.session()"""
    async with db_session_manager.session() as session:
        yield session


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    async with redis_manager.session() as session:
        yield session


RedisDep = Annotated[Redis, Depends(get_redis_client)]


async def get_http_client() -> AsyncClient:
    return await http_client_manager.client()


HTTPClientDep = Annotated[AsyncClient, Depends(get_http_client)]
