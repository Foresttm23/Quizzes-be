import uuid

from fastapi import APIRouter, status, Query

from app.core.dependencies import DBSessionDep
from app.schemas.user_schema import SignUpRequest, UserInfoUpdateRequest, UserDetailsResponse, PaginationResponse, \
    UserPasswordUpdateRequest
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", status_code=status.HTTP_200_OK, response_model=PaginationResponse[UserDetailsResponse])
async def get_users(db: DBSessionDep, page: int = Query(ge=1), page_size: int = Query(ge=1)):
    """Endpoint for getting users with pagination"""
    user_service = UserService(db=db)
    users = await user_service.fetch_instances_paginated(page=page, page_size=page_size)
    return users


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def get_user(db: DBSessionDep, user_id: uuid.UUID):
    """Endpoint for getting a user by id"""
    user_service = UserService(db=db)
    user = await user_service.fetch_instance(instance_id=user_id)
    return user


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserDetailsResponse)
async def create_user(db: DBSessionDep, user_info: SignUpRequest):
    """Endpoint for creating a user"""
    user_service = UserService(db=db)
    user = await user_service.create_user(user_info=user_info)
    return user


@router.put("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def update_user_info(db: DBSessionDep, user_id: uuid.UUID, new_user_info: UserInfoUpdateRequest):
    """Endpoint for updating user info by id"""
    user_service = UserService(db=db)
    user = await user_service.update_user_info(user_id=user_id, new_user_info=new_user_info)
    return user


@router.put("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def update_user_password(db: DBSessionDep, user_id: uuid.UUID, new_password_info: UserPasswordUpdateRequest):
    """Endpoint for updating user password by id"""
    user_service = UserService(db=db)
    user = await user_service.update_user_password(user_id=user_id, new_password_info=new_password_info)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(db: DBSessionDep, user_id: uuid.UUID):
    """Endpoint for deleting a user by id"""
    user_service = UserService(db=db)
    await user_service.delete_instance(instance_id=user_id)
