from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import (redis as redis_module, postgres as postgres_module)
from app.services.auth_service import AuthService
from app.services.user_service import UserService

RedisDep = Annotated[Redis, Depends(redis_module.get_redis_client)]

DBSessionDep = Annotated[AsyncSession, Depends(postgres_module.get_db_session)]

security = HTTPBearer()
SecurityDep = Annotated[HTTPAuthorizationCredentials, Depends(security)]


def get_jwt_from_header(header: SecurityDep) -> str:
    jwt = header.credentials
    return jwt


JWTCredentialsDep = Annotated[str, Depends(get_jwt_from_header)]


async def get_user_service(db: DBSessionDep) -> UserService:
    return UserService(db=db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_auth_service(user_service: UserServiceDep) -> AuthService:
    return AuthService(user_service=user_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_jwt_payload_from_header(jwt: JWTCredentialsDep, auth_service: AuthServiceDep) -> dict:
    jwt_payload = auth_service.verify_token_and_get_payload(jwt_token=jwt)
    return jwt_payload


LoginJWTDep = Annotated[dict, Depends(get_jwt_payload_from_header)]


async def get_local_jwt_payload_from_header(jwt: JWTCredentialsDep, auth_service: AuthServiceDep) -> dict:
    jwt_payload = auth_service.verify_local_token_and_get_payload(jwt_token=jwt)
    return jwt_payload


LocalJWTDep = Annotated[dict, Depends(get_local_jwt_payload_from_header)]
