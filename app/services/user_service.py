import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.security import hash_password
from app.db.models.user import User as UserModel
from app.schemas.user_schema import SignUpRequest, UserUpdateRequest
from app.utils.db_helpers import get_user_or_404, save_changes_and_refresh, apply_updates, get_items_paginated


async def get_users_crud(page: int, page_size: int, db: AsyncSession):
    """Crud for getting all users"""
    users = await get_items_paginated(db=db, model=UserModel, page=page, page_size=page_size)
    return users


async def get_user_crud(user_id: uuid.UUID, db: AsyncSession):
    """Crud for getting a user by id"""
    user = await get_user_or_404(db=db, user_id=user_id)
    return user


async def create_user_crud(user_info: SignUpRequest, db: AsyncSession):
    """Crud for creating a user"""
    plain_password = user_info.password.get_secret_value()
    hashed_password = hash_password(plain_password)

    # Since we don't want to commit real password from the user_info fields
    # We specify directly what fields we need
    user = UserModel(
        email=user_info.email,
        username=user_info.username,
        hashed_password=hashed_password
    )

    await save_changes_and_refresh(db=db, instance=user)

    logger.info(f"Created new User: {user.id}")

    return user


async def update_user_crud(user_id: uuid.UUID, new_user_info: UserUpdateRequest, db: AsyncSession):
    """Crud for updating user details by id"""
    user = await get_user_or_404(db=db, user_id=user_id)

    changes = apply_updates(user=user, data=new_user_info)

    # If not changes return user from db
    if not changes:
        return user

    await save_changes_and_refresh(db=db, instance=user)

    logger.info(f"Updated User: {user.id}")
    logger.debug(f"User: {user.id}, updated: {changes}")

    return user


async def delete_user_crud(user_id: uuid.UUID, db: AsyncSession) -> None:
    """Crud for deleting a user by id"""
    user = await get_user_or_404(db=db, user_id=user_id)

    logger.info(f"Deleted User: {user.id}")

    await db.delete(user)
    await db.commit()
