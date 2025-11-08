import uuid

from fastapi import APIRouter, status
from fastapi import Query

from app.core.dependencies import DBSessionDep, JWTDep
from app.schemas.user_schemas.user_request_schema import UserInfoUpdateRequest, UserPasswordUpdateRequest
from app.schemas.user_schemas.user_response_schema import PaginationResponse
from app.schemas.user_schemas.user_response_schema import UserDetailsResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", status_code=status.HTTP_200_OK, response_model=PaginationResponse[UserDetailsResponse])
async def get_users(db: DBSessionDep, page: int = Query(ge=1), page_size: int = Query(ge=1)):
    """Endpoint for getting users with pagination"""
    user_service = UserService(db=db)
    users = await user_service.fetch_instances_paginated(page=page, page_size=page_size)
    return users


# Must be defined before the more general /{user_id} endpoint
# Otherwise, a request to /me would be interpreted as /{user_id}
@router.get("/me", response_model=UserDetailsResponse, status_code=status.HTTP_200_OK)
async def get_me(db: DBSessionDep, jwt_payload: JWTDep):
    user_service = UserService(db=db)
    user = await user_service.fetch_instance(field_name="email", field_value=jwt_payload["email"])
    return user


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def get_user(db: DBSessionDep, user_id: uuid.UUID):
    """Endpoint for getting a user by id"""
    user_service = UserService(db=db)
    user = await user_service.fetch_instance(field_name="id", field_value=user_id)
    return user


@router.patch("/me/info", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def update_self_info(db: DBSessionDep, jwt_payload: JWTDep,
                           new_user_info: UserInfoUpdateRequest):
    """
    Endpoint for updating user info by id.
    Only allows to input fields from
    UserInfoUpdateRequest schema.
    """
    user_service = UserService(db=db)
    user = await user_service.update_user_info(user_id=jwt_payload["id"], new_user_info=new_user_info)
    return user


@router.patch("/me/password", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def update_self_password(db: DBSessionDep, jwt_payload: JWTDep,
                               new_password_info: UserPasswordUpdateRequest):
    """
    Endpoint for updating user password by id.
    Only allows to input fields from
    UserPasswordUpdateRequest schema.
    """
    user_service = UserService(db=db)
    user = await user_service.update_user_password(user_id=jwt_payload["id"], new_password_info=new_password_info)
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_self(db: DBSessionDep, jwt_payload: JWTDep):
    """Endpoint for deleting a user by id"""
    user_service = UserService(db=db)
    await user_service.delete_instance_by_id(instance_id=jwt_payload["id"])
