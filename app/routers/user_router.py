import uuid

from fastapi import APIRouter, status, Query

from app.core.config import settings
from app.core.dependencies import LocalJWTDep, UserServiceDep
from app.schemas.base_schemas import PaginationResponse
from app.schemas.user_schemas.user_request_schema import UserInfoUpdateRequest, UserPasswordUpdateRequest
from app.schemas.user_schemas.user_response_schema import UserDetailsResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", status_code=status.HTTP_200_OK, response_model=PaginationResponse[UserDetailsResponse])
async def get_users(user_service: UserServiceDep, page: int = Query(ge=1),
                    page_size: int = Query(ge=1, le=settings.APP.MAX_PAGE_SIZE)):
    """Return a list of all users by page and page_size"""
    users = await user_service.fetch_users_data_paginated(page=page, page_size=page_size)
    return users


# Must be defined before the more general /{user_id} endpoint
# Otherwise, a request to /me would be interpreted as /{user_id}
@router.get("/me", response_model=UserDetailsResponse, status_code=status.HTTP_200_OK)
async def get_me(user_service: UserServiceDep, jwt_payload: LocalJWTDep):
    """Returns an authenticated user info"""
    user = await user_service.fetch_user(field_name="email", field_value=jwt_payload["email"])
    return user


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def get_user(user_service: UserServiceDep, user_id: uuid.UUID):
    """Returns a user by its id"""
    user = await user_service.fetch_user(field_name="id", field_value=user_id)
    return user


@router.patch("/me/info", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def update_self_info(user_service: UserServiceDep, jwt_payload: LocalJWTDep,
                           new_user_info: UserInfoUpdateRequest):
    """Updates info for authenticated user"""
    user = await user_service.update_user_info(user_email=jwt_payload["email"], new_user_info=new_user_info)
    return user


@router.patch("/me/password", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def update_self_password(user_service: UserServiceDep, jwt_payload: LocalJWTDep,
                               new_password_info: UserPasswordUpdateRequest):
    """Updates password for authenticated user"""
    user = await user_service.update_user_password(user_email=jwt_payload["email"], new_password_info=new_password_info)
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_self(user_service: UserServiceDep, jwt_payload: LocalJWTDep):
    """Deletes currently authenticated user"""
    await user_service.delete_user(user_email=jwt_payload["email"])
