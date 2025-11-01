import uuid
from typing import Type, TypeVar

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.db.models.user import User as UserModel
from app.schemas.user import UserUpdateRequest

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
        raise HTTPException(status_code=400, detail="Record already exists")

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
        raise HTTPException(status_code=404, detail="User not found")
    return user


def apply_updates(user: UserModel, data: UserUpdateRequest) -> dict:
    """
    Helper function for updating user details.
    Takes user and data, that represents new user details if filled.
    model_dump for SecretStr returns "*****" so accident password leakage is prevented.
    """
    changes = {}

    # If a field exists and not None
    if "password" in data.model_fields_set:
        hashed_password = hash_password(data.password.get_secret_value())
        setattr(user, "hashed_password", hashed_password)
        changes["password"] = {"updated": True}

    update_data = data.model_dump(exclude_unset=True)
    for key, new_value in update_data.items():
        if key == "password":
            continue
        old_value = getattr(user, key)
        if old_value != new_value:
            changes[key] = {"from": old_value, "to": new_value}
            setattr(user, key, new_value)

    return changes
