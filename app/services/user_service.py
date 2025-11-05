import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.security import hash_password
from app.db.models.user import User as UserModel
from app.db.repository.user_repository import get_user_or_404, save_changes_and_refresh, apply_user_updates, \
    get_items_paginated, delete_user, apply_password_updates
from app.schemas.user_schema import SignUpRequest, UserInfoUpdateRequest, UserPasswordUpdateRequest


async def get_users_service(page: int, page_size: int, db: AsyncSession):
    """Method for getting all users"""
    users = await get_items_paginated(db=db, model=UserModel, page=page, page_size=page_size)
    return users


async def get_user_service(user_id: uuid.UUID, db: AsyncSession):
    """Method for getting a user by id"""
    user = await get_user_or_404(db=db, user_id=user_id)
    return user


async def create_user_service(user_info: SignUpRequest, db: AsyncSession):
    """Method for creating a user"""
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


async def update_user_info_service(user_id: uuid.UUID, new_user_info: UserInfoUpdateRequest, db: AsyncSession):
    """Method for updating user details by id"""
    user = await get_user_or_404(db=db, user_id=user_id)

    changes = apply_user_updates(user=user, new_user_info=new_user_info)

    # If not changes return user from db
    if not changes:
        return user

    await save_changes_and_refresh(db=db, instance=user)

    logger.info(f"Updated User: {user.id}")
    logger.debug(f"User: {user.id}, updated: {changes}")

    return user


async def update_user_password_service(user_id: uuid.UUID, new_password_info: UserPasswordUpdateRequest,
                                       db: AsyncSession):
    """Method for updating user password by id"""
    user = await get_user_or_404(db=db, user_id=user_id)
    password_changed = apply_password_updates(user=user, new_password_info=new_password_info)

    if not password_changed:
        return user

    await save_changes_and_refresh(db=db, instance=user)

    logger.info(f"Updated User: {user.id}")
    logger.debug(f"User: {user.id}, changed password")

    return user


async def delete_user_service(user_id: uuid.UUID, db: AsyncSession) -> None:
    """Method for deleting a user by id"""
    user = await get_user_or_404(db=db, user_id=user_id)

    logger.info(f"Deleted User: {user.id}")

    await delete_user(db, user)
