import uuid

from fastapi import APIRouter, status
from fastapi import Query

from app.core.dependencies import JWTDep, UserServiceDep
from app.schemas.user_schemas.user_request_schema import UserInfoUpdateRequest, UserPasswordUpdateRequest
from app.schemas.user_schemas.user_response_schema import PaginationResponse
from app.schemas.user_schemas.user_response_schema import UserDetailsResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", status_code=status.HTTP_200_OK, response_model=PaginationResponse[UserDetailsResponse])
async def get_users(user_service: UserServiceDep, page: int = Query(ge=1), page_size: int = Query(ge=1)):
    """Endpoint for getting users with pagination"""

    users = await user_service.fetch_users_data_paginated(page=page, page_size=page_size)
    return users


# Must be defined before the more general /{user_id} endpoint
# Otherwise, a request to /me would be interpreted as /{user_id}
@router.get("/me", response_model=UserDetailsResponse, status_code=status.HTTP_200_OK)
async def get_me(user_service: UserServiceDep, jwt_payload: JWTDep):
    user = await user_service.fetch_user(field_name="email", field_value=jwt_payload["email"])
    return user


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def get_user(user_service: UserServiceDep, user_id: uuid.UUID):
    """Endpoint for getting a user by id"""
    user = await user_service.fetch_user(field_name="id", field_value=user_id)
    return user


@router.patch("/me/info", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def update_self_info(user_service: UserServiceDep, jwt_payload: JWTDep,
                           new_user_info: UserInfoUpdateRequest):
    """
    Endpoint for updating user info by id.
    Only allows to input fields from
    UserInfoUpdateRequest schema.
    """
    user = await user_service.update_user_info(user_id=jwt_payload["id"], new_user_info=new_user_info)
    return user


@router.patch("/me/password", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def update_self_password(user_service: UserServiceDep, jwt_payload: JWTDep,
                               new_password_info: UserPasswordUpdateRequest):
    """
    Endpoint for updating user password by id.
    Only allows to input fields from
    UserPasswordUpdateRequest schema.
    """
    user = await user_service.update_user_password(user_id=jwt_payload["id"], new_password_info=new_password_info)
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_self(user_service: UserServiceDep, jwt_payload: JWTDep):
    """Endpoint for deleting a user by id"""
    await user_service.delete_user_by_id(user_id=jwt_payload["id"])
