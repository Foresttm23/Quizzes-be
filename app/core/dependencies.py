from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import (redis as redis_module, postgres as postgres_module)

RedisDep = Annotated[Redis, Depends(redis_module.get_redis_client)]

DBSessionDep = Annotated[AsyncSession, Depends(postgres_module.get_db_session)]
