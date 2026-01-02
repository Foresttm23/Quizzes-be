from uuid import UUID

from app.schemas.user_schemas.user_request_schema import UserInfoUpdateRequest, UserPasswordUpdateRequest
from app.schemas.user_schemas.user_response_schema import UserDetailsResponse
from fastapi import APIRouter, status, Query

from app.core.config import settings
from app.core.dependencies import GetUserJWTDep, UserServiceDep
from app.core.exceptions import ExternalAuthProviderException
from app.schemas.base_schemas import PaginationResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", status_code=status.HTTP_200_OK, response_model=PaginationResponse[UserDetailsResponse])
async def get_users(user_service: UserServiceDep, page: int = Query(default=1, ge=1),
                    page_size: int = Query(default=10, ge=1, le=settings.APP.MAX_PAGE_SIZE)):
    """Return a list of all users by page and page_size"""
    users = await user_service.get_users_paginated(page=page, page_size=page_size)
    return users


# Must be defined before the more general /{user_id} endpoint
# Otherwise, a request to /me would be interpreted as /{user_id}
@router.get("/me", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def get_me(user: GetUserJWTDep):
    """Returns an authenticated user info"""
    return user


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def get_user(user_service: UserServiceDep, user_id: UUID):
    """Returns a user by its id"""
    user = await user_service.get_by_id(user_id=user_id)
    return user


@router.patch("/me/info", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def update_self_info(user_service: UserServiceDep, user: GetUserJWTDep, new_user_info: UserInfoUpdateRequest):
    """Updates info for authenticated user"""
    user = await user_service.update_user_info(user=user, new_user_info=new_user_info)
    return user


@router.patch("/me/password", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def update_self_password(user_service: UserServiceDep, user: GetUserJWTDep,
                               new_password_info: UserPasswordUpdateRequest):
    """Updates password for authenticated user"""
    if user.auth_provider != "local":
        raise ExternalAuthProviderException(auth_provider=user.auth_provider,
                                            message="change password in your provider")

    user = await user_service.update_user_password(user=user, new_password_info=new_password_info)
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_self(user_service: UserServiceDep, user: GetUserJWTDep):
    """Deletes currently authenticated user"""
    await user_service.delete_user(user=user)
