import uuid
from typing import Type, TypeVar, Generic

from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import RecordAlreadyExistsException, InstanceNotFoundException
from app.db.postgres import Base

ModelType = TypeVar("ModelType", bound=Base)
SchemaType = TypeVar("SchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_instances_paginated(self, page: int, page_size: int) -> dict:
        """Returns a dict of instances in specified range and metadata"""
        page = max(page, 1)
        page_size = max(min(page_size, settings.APP.MAX_PAGE_SIZE), 1)

        offset = (page - 1) * page_size

        result = await self.db.execute(select(self.model).offset(offset).limit(page_size))
        items = result.scalars().all()

        total_result = await self.db.execute(select(func.count()).select_from(self.model))
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

    async def commit_with_handling(self, instance: ModelType | None = None) -> None:
        """
        Commits current state of commits and refreshes instance.
        If instance is None only commits.
        If there is duplicate of unique field, IntegrityError is called.
        """
        try:
            await self.db.commit()
        except IntegrityError:
            raise RecordAlreadyExistsException()

        if instance:
            await self.db.refresh(instance)

    async def save_changes_and_refresh(self, instance: ModelType) -> None:
        """
        Wrapper for commit_with_handling() that also adds an instance to db.
        """
        self.db.add(instance)
        await self.commit_with_handling(instance=instance)

    async def get_instance_or_404(self, instance_id: uuid.UUID) -> ModelType:
        """
        Gets instance by ID.
        If no instance exists, raise error.
        Else returns instance.
        """
        instance = await self.db.get(self.model, instance_id)
        if not instance:
            raise InstanceNotFoundException()
        return instance

    @staticmethod
    def apply_instance_updates(instance: ModelType, new_instance_info: SchemaType) -> dict:
        """
        Helper function for updating instance details and keeping track of changes.
        Takes instance and new_instance_info.
        """
        changes = {}

        update_data = new_instance_info.model_dump(exclude_unset=True)
        for key, new_value in update_data.items():
            old_value = getattr(instance, key)
            if old_value != new_value:
                changes[key] = {"from": old_value, "to": new_value}
                setattr(instance, key, new_value)

        return changes

    async def delete_instance(self, instance: ModelType) -> None:
        """
        Function to delete instance and commit changes.
        """
        await self.db.delete(instance)
        # We don't provide a value, since we don't need neither to update nor return user
        await self.commit_with_handling()
