from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

import database as postgres_module
from core import redis as redis_module
from core.redis import Redis

DBSessionDep = Annotated[AsyncSession, Depends(postgres_module.get_db_session)]
RedisDep = Annotated[Redis, Depends(redis_module.get_redis_client)]
