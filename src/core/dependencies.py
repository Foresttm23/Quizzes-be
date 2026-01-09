from dataclasses import dataclass
from typing import Annotated, AsyncGenerator

from exceptions import DBSessionNotInitializedException
from fastapi import Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from . import database as postgres_module
from . import redis as redis_module
from .config import settings


@dataclass
class PaginationParams:
    page: int = Query(default=1, ge=1, description="Page number")
    page_size: int = Query(
        default=10,
        ge=1,
        le=settings.APP.MAX_PAGE_SIZE,
        description="Number of items per page",
    )


PaginationParamDep = Annotated[PaginationParams, Depends()]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if postgres_module.sessionmanager is None:
        raise DBSessionNotInitializedException()
    async with postgres_module.sessionmanager.session() as session:
        yield session


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_redis_session() -> AsyncGenerator[Redis, None]:
    if redis_module.redis_pool is None:
        raise  # TODO
    redis_client = Redis(connection_pool=redis_module.redis_pool)
    try:
        yield redis_client
    finally:
        await redis_client.close()


RedisDep = Annotated[Redis, Depends(get_redis_session)]
