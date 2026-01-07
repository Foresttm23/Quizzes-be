from dataclasses import dataclass
from typing import Annotated

from fastapi import Query, Depends
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from . import database as postgres_module, redis as redis_module
from .config import settings

DBSessionDep = Annotated[AsyncSession, Depends(postgres_module.get_db_session)]
RedisDep = Annotated[Redis, Depends(redis_module.get_redis_client)]


@dataclass
class PaginationParams:
    page: int = Query(default=1, ge=1, description="Page number")
    page_size: int = Query(default=10, ge=1, le=settings.APP.MAX_PAGE_SIZE, description="Number of items per page")


PaginationParamDep = Annotated[PaginationParams, Depends()]
