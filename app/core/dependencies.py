from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import (redis as redis_module, postgres as postgres_module)
from app.db.models.user_model import User as UserModel
from app.services.auth_service import AuthService
from app.services.company_service import CompanyService
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


async def get_company_service(db: DBSessionDep, user_service: UserServiceDep) -> CompanyService:
    return CompanyService(db=db, user_service=user_service)


CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]


async def get_user_from_jwt(jwt: JWTCredentialsDep, auth_service: AuthServiceDep) -> UserModel:
    jwt_payload = auth_service.verify_token_and_get_payload(jwt_token=jwt)
    user = await auth_service.handle_jwt_sign_in(jwt_payload=jwt_payload)
    return user


GetUserJWTDep = Annotated[UserModel, Depends(get_user_from_jwt)]


async def get_user_from_refresh_jwt(jwt: JWTCredentialsDep,
                                    auth_service: AuthServiceDep, user_service: UserServiceDep) -> UserModel:
    jwt_refresh_payload = auth_service.verify_refresh_token_and_get_payload(token=jwt)
    user = await user_service.fetch_user(field_name="id", field_value=jwt_refresh_payload["id"])
    return user


GetUserRefreshJWTDep = Annotated[UserModel, Depends(get_user_from_refresh_jwt)]
