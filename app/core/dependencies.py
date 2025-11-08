from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_local_token_and_get_payload, verify_token_and_get_payload
from app.db import (redis as redis_module, postgres as postgres_module)

RedisDep = Annotated[Redis, Depends(redis_module.get_redis_client)]

DBSessionDep = Annotated[AsyncSession, Depends(postgres_module.get_db_session)]

VerifyLocalTokenAndGetPayloadDep = Annotated[dict, Depends(verify_local_token_and_get_payload)]

security = HTTPBearer()
SecurityDep = Annotated[HTTPAuthorizationCredentials, Depends(security)]


async def get_jwt_from_header(header: SecurityDep) -> dict:
    jwt = header.credentials
    jwt_payload = verify_token_and_get_payload(jwt)
    return jwt_payload


JWTDep = Annotated[dict, Depends(get_jwt_from_header)]
