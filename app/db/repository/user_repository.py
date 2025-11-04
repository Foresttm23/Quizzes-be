import uuid
from typing import Type, TypeVar

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import RecordAlreadyExistsException, InstanceNotFoundException, PasswordReuseException
from app.core.security import hash_password, verify_password
from app.db.models.user import User as UserModel
from app.schemas.user_schema import UserInfoUpdateRequest, UserPasswordUpdateRequest

ModelType = TypeVar("ModelType")


async def get_items_paginated(db: AsyncSession, model: Type[ModelType], page: int, page_size: int) -> dict:
    page = max(page, 1)
    page_size = max(min(page_size, settings.APP.MAX_PAGE_SIZE), 1)

    offset = (page - 1) * page_size

    result = await db.execute(select(model).offset(offset).limit(page_size))
    items = result.scalars().all()

    total_result = await db.execute(select(func.count()).select_from(model))
    total = total_result.scalar() or 0

    total_pages = (total + page_size - 1) // page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "data": items,
    }


async def commit_with_handling(db: AsyncSession, instance=None):
    """
    Commits current state of commits and refreshes instance.
    If instance is None only commits.
    If there is duplicate of unique field, IntegrityError is called.
    """
    try:
        await db.commit()
    except IntegrityError:
        raise RecordAlreadyExistsException()

    if instance:
        await db.refresh(instance)


async def save_changes_and_refresh(db: AsyncSession, instance: UserModel) -> None:
    """
    Wrapper for commit_with_handling() that also adds an instance to db.
    """
    db.add(instance)
    await commit_with_handling(db=db, instance=instance)


async def get_user_or_404(db: AsyncSession, user_id: uuid.UUID) -> UserModel:
    """
    Gets user by ID.
    If no user exists, raise error.
    Else returns user
    """
    user = await db.get(UserModel, user_id)
    if not user:
        raise InstanceNotFoundException()
    return user


def apply_user_updates(user: UserModel, new_user_info: UserInfoUpdateRequest) -> dict:
    """
    Helper function for updating user details and keeping track of changes.
    Takes user and new_user_info.
    Doesn't include password field.
    Password change has different method.
    """
    changes = {}

    update_data = new_user_info.model_dump(exclude_unset=True)
    for key, new_value in update_data.items():
        old_value = getattr(user, key)
        if old_value != new_value:
            changes[key] = {"from": old_value, "to": new_value}
            setattr(user, key, new_value)

    return changes


def apply_password_updates(user: UserModel, new_password_info: UserPasswordUpdateRequest) -> bool:
    """
    Helper function for updating user password and keeping track of changes.
    Takes user and new_password_info.
    """
    current_password = new_password_info.current_password.get_secret_value()
    new_password = new_password_info.new_password.get_secret_value()

    # As long as current and new are the same, we raise exception.
    if current_password == new_password:
        raise PasswordReuseException()

    if not verify_password(current_password, user.hashed_password):
        return False

    user.hashed_password = hash_password(new_password)
    return True


async def delete_user(db: AsyncSession, user: UserModel) -> None:
    """
    Function to delete user and commit changes.
    """
    await db.delete(user)
    # We don't provide a value, since we don't need neither to update nor return user
    await commit_with_handling(db=db, instance=None)
