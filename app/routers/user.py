import uuid

from fastapi import APIRouter, status, Query

from app.core.dependencies import DBSessionDep
from app.crud.user import get_user_crud, get_users_crud, create_user_crud, update_user_crud, delete_user_crud
from app.schemas.user import SignUpRequest, UserUpdateRequest, UserDetailsResponse, PaginationResponse

router = APIRouter(prefix="/users", tags=["users"])


# TODO add custom Error handling


@router.get("/", status_code=status.HTTP_200_OK, response_model=PaginationResponse[UserDetailsResponse])
async def get_users(db: DBSessionDep, page: int = Query(ge=1), page_size: int = Query(ge=1)):
    """Endpoint for getting users with pagination"""
    users = await get_users_crud(page=page, page_size=page_size, db=db)
    return users


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def get_user(db: DBSessionDep, user_id: uuid.UUID):
    """Endpoint for getting a user by id"""
    user = await get_user_crud(user_id, db)
    return user


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserDetailsResponse)
async def create_user(db: DBSessionDep, user_info: SignUpRequest):
    """Endpoint for creating a user"""
    user = await create_user_crud(user_info, db)
    return user


@router.put("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserDetailsResponse)
async def update_user(db: DBSessionDep, user_id: uuid.UUID, new_user_info: UserUpdateRequest):
    """Endpoint for updating user details by id"""
    user = await update_user_crud(user_id, new_user_info, db)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(db: DBSessionDep, user_id: uuid.UUID):
    """Endpoint for deleting a user by id"""
    await delete_user_crud(user_id, db)
