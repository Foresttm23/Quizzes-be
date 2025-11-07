from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token
from app.db import (redis as redis_module, postgres as postgres_module)

RedisDep = Annotated[Redis, Depends(redis_module.get_redis_client)]

DBSessionDep = Annotated[AsyncSession, Depends(postgres_module.get_db_session)]

VerifyTokenDep = Annotated[dict, Depends(verify_token)]

OAuth2PasswordRequestFormDep = Annotated[OAuth2PasswordRequestForm, Depends()]
