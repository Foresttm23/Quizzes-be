from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_limiter.depends import RateLimiter

from src.core.config import settings
from src.core.dependencies import DBSessionDep, HTTPClientDep
from src.core.exceptions import NotAuthenticatedException

from .models import User as UserModel
from .service import AuthService, TokenService, UserService

AuthLimitDep = Depends(RateLimiter(times=5, seconds=60))
UserLimitDep = Depends(RateLimiter(times=5, seconds=60))

security = HTTPBearer(auto_error=False)
SecurityDep = Annotated[HTTPAuthorizationCredentials, Depends(security)]


def get_jwt_from_header(header: SecurityDep) -> str | None:
    if header:
        return header.credentials
    else:
        return None


JWTCredentialsDep = Annotated[str, Depends(get_jwt_from_header)]


async def get_user_service(db: DBSessionDep) -> UserService:
    return UserService(db=db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_token_service(http_client: HTTPClientDep) -> TokenService:
    return TokenService(
        http_client=http_client,
        local_settings=settings.LOCAL_JWT,
        auth0_settings=settings.AUTH0_JWT,
    )


TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


async def get_auth_service(user_service: UserServiceDep) -> AuthService:
    return AuthService(user_service=user_service, app_settings=settings.APP)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_optional_user_from_jwt(
    jwt: JWTCredentialsDep, token_service: TokenServiceDep, auth_service: AuthServiceDep
) -> UserModel | None:
    if not jwt:
        return None
    jwt_payload = await token_service.verify_token_and_get_payload(jwt_token=jwt)
    user = await auth_service.handle_jwt_sign_in(jwt_payload=jwt_payload)
    return user


GetOptionalUserJWTDep = Annotated[UserModel, Depends(get_optional_user_from_jwt)]


async def get_user_from_jwt(user: GetOptionalUserJWTDep) -> UserModel:
    if not user:
        raise NotAuthenticatedException()
    return user


GetUserJWTDep = Annotated[UserModel, Depends(get_user_from_jwt)]


async def get_user_from_refresh_jwt(
    jwt: JWTCredentialsDep,
    token_service: TokenServiceDep,
    user_service: UserServiceDep,
) -> UserModel:
    jwt_refresh_payload = token_service.verify_refresh_token_and_get_payload(token=jwt)
    user = await user_service.get_by_id_model(user_id=UUID(jwt_refresh_payload.sub))
    return user


GetUserRefreshJWTDep = Annotated[UserModel, Depends(get_user_from_refresh_jwt)]
