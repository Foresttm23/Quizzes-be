from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.dependencies import DBSessionDep
from core.exceptions import NotAuthenticatedException
from .models import User as UserModel
from .service import AuthService, UserService

security = HTTPBearer(auto_error=False)
SecurityDep = Annotated[HTTPAuthorizationCredentials, Depends(security)]


def get_jwt_from_header(header: SecurityDep) -> str:
    if header:
        jwt = header.credentials
    else:
        jwt = None
    return jwt


JWTCredentialsDep = Annotated[str, Depends(get_jwt_from_header)]


async def get_user_service(db: DBSessionDep) -> UserService:
    return UserService(db=db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_auth_service(user_service: UserServiceDep) -> AuthService:
    return AuthService(user_service=user_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_user_from_jwt(jwt: JWTCredentialsDep, auth_service: AuthServiceDep) -> UserModel:
    if not jwt:
        raise NotAuthenticatedException()
    jwt_payload = auth_service.verify_token_and_get_payload(jwt_token=jwt)
    user = await auth_service.handle_jwt_sign_in(jwt_payload=jwt_payload)
    return user


GetUserJWTDep = Annotated[UserModel, Depends(get_user_from_jwt)]


async def get_optional_user_from_jwt(jwt: JWTCredentialsDep, auth_service: AuthServiceDep) -> UserModel | None:
    if not jwt:
        return None
    jwt_payload = auth_service.verify_token_and_get_payload(jwt_token=jwt)
    user = await auth_service.handle_jwt_sign_in(jwt_payload=jwt_payload)
    return user


GetOptionalUserJWTDep = Annotated[UserModel, Depends(get_optional_user_from_jwt)]


async def get_user_from_refresh_jwt(jwt: JWTCredentialsDep, auth_service: AuthServiceDep,
                                    user_service: UserServiceDep) -> UserModel:
    jwt_refresh_payload = auth_service.verify_refresh_token_and_get_payload(token=jwt)
    user = await user_service.get_by_id(user_id=jwt_refresh_payload["id"])
    return user


GetUserRefreshJWTDep = Annotated[UserModel, Depends(get_user_from_refresh_jwt)]
