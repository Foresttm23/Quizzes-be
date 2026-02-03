from uuid import UUID

from fastapi import APIRouter, Response, status
from fastapi_cache.decorator import cache

from src.core.caching.keys import endpoint_key_builder
from src.core.dependencies import PaginationParamDep
from src.core.exceptions import ExternalAuthProviderException
from src.core.schemas import PaginationResponse
from src.quiz.dependencies import AttemptServiceDep

from .dependencies import (
    AuthLimitDep,
    AuthServiceDep,
    GetUserJWTDep,
    GetUserRefreshJWTDep,
    TokenServiceDep,
    UserLimitDep,
    UserServiceDep,
)
from .schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserAverageSystemStatsResponseSchema,
    UserDetailsResponse,
    UserInfoUpdateRequest,
    UserPasswordUpdateRequest,
)

# These limits are router based, so all routers endpoints will share the same limit.
auth_router = APIRouter(prefix="/auth", tags=["Auth"], dependencies=[AuthLimitDep])
users_router = APIRouter(prefix="/users", tags=["Users"], dependencies=[UserLimitDep])


@auth_router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserDetailsResponse
)
async def register(auth_service: AuthServiceDep, register_data: RegisterRequest):
    """Endpoint for registering/creating a user"""
    user = await auth_service.register_user(sign_up_data=register_data)
    return user


@auth_router.post(
    "/login", response_model=TokenResponse, status_code=status.HTTP_200_OK
)
async def login(
    response: Response,
    token_service: TokenServiceDep,
    auth_service: AuthServiceDep,
    login_data: LoginRequest,
):
    """
    Endpoint for authenticating a user with password and email.
    For Auth0 log in call users/me or any with GetUserJWTDep.
    """
    user = await auth_service.handle_email_password_sign_in(sign_in_data=login_data)
    tokens = token_service.create_token_pairs(user=user)

    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        max_age=1800,
        expires=1800,
        samesite="lax",
        secure=True,  # HTTPS
    )

    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        path="/auth/refresh",
        samesite="lax",
        secure=True,  # HTTPS
    )

    return tokens


@auth_router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/auth")
    response.delete_cookie("refresh_token", path="/auth/refresh")
    return {"message": "Logged out"}


@auth_router.post(
    "/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK
)
async def refresh_jwt(token_service: TokenServiceDep, user: GetUserRefreshJWTDep):
    """
    Endpoint for refreshing a refresh token.
    Accepts refresh token.
    Returns both, refresh token and access token.
    """
    # Technically never raised, since external providers cannot be decoded with the local configuration.
    if user.auth_provider != "local":
        raise ExternalAuthProviderException(
            auth_provider=user.auth_provider, message="no local tokens issued"
        )

    tokens = token_service.create_token_pairs(user=user)
    return tokens


@users_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=PaginationResponse[UserDetailsResponse],
)
@cache(expire=600, key_builder=endpoint_key_builder)
async def get_users(user_service: UserServiceDep, pagination: PaginationParamDep):
    """Return a list of all users by page and page_size"""
    users = await user_service.get_users_paginated(
        page=pagination.page, page_size=pagination.page_size
    )
    return users


# Must be defined before the more general /{user_id} endpoint
# Otherwise, a request to /me would be interpreted as /{user_id}
@users_router.get(
    "/me", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse
)
@cache(expire=600, key_builder=endpoint_key_builder)
async def get_me(user: GetUserJWTDep):
    """Returns an authenticated user info"""
    return user


@users_router.get(
    "/{user_id}", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse
)
@cache(expire=600, key_builder=endpoint_key_builder)
async def get_user(user_service: UserServiceDep, user_id: UUID):
    """Returns a user by its id"""
    user = await user_service.get_by_id(user_id=user_id)
    return user


@users_router.patch(
    "/me/info", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse
)
async def update_self_info(
    user_service: UserServiceDep,
    user: GetUserJWTDep,
    new_user_info: UserInfoUpdateRequest,
):
    """Updates info for authenticated user"""
    user = await user_service.update_user_info(user=user, new_user_info=new_user_info)
    return user


@users_router.patch(
    "/me/password", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse
)
async def update_self_password(
    user_service: UserServiceDep,
    user: GetUserJWTDep,
    new_password_info: UserPasswordUpdateRequest,
):
    """Updates password for authenticated user"""
    if user.auth_provider != "local":
        raise ExternalAuthProviderException(
            auth_provider=user.auth_provider, message="change password in your provider"
        )

    user = await user_service.update_user_password(
        user=user, new_password_info=new_password_info
    )
    return user


@users_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_self(user_service: UserServiceDep, user: GetUserJWTDep):
    """Deletes currently authenticated user"""
    await user_service.delete_user(user=user)


@users_router.get(
    "/me/system-average-score",
    response_model=UserAverageSystemStatsResponseSchema,
    status_code=status.HTTP_200_OK,
)
@cache(expire=3600, key_builder=endpoint_key_builder)
async def get_user_average_score_system_wide(
    attempt_service: AttemptServiceDep, user: GetUserJWTDep
):
    stats = await attempt_service.get_user_stats_system_wide(user_id=user.id)
    return stats
