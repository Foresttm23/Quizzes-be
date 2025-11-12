from http.client import HTTPException
from typing import Type, TypeVar, Generic, Any

from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.selectable import Select

from app.core.config import settings
from app.core.exceptions import RecordAlreadyExistsException, InstanceNotFoundException, \
    InvalidSQLModelFieldNameException
from app.db.postgres import Base

ModelType = TypeVar("ModelType", bound=Base)
SchemaType = TypeVar("SchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_instances_data_paginated(self, page: int, page_size: int,
                                           filters: dict[str, Any] | None = None) -> dict:
        """
        Returns a dict of instances and metadata in specified range.
        Can accept filter fields in format {"field_name": value}.
        """
        page = max(page, 1)
        page_size = max(min(page_size, settings.APP.MAX_PAGE_SIZE), 1)

        offset = (page - 1) * page_size

        conditions, query = self._apply_filters(filters=filters)

        # This queries adds on top of the previous queries,
        # so in the end we will get a final query to execute
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        count_query = select(func.count()).select_from(self.model)
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total = (await self.db.execute(count_query)).scalar() or 0
        total_pages = (total + page_size - 1) // page_size

        return {"total": total, "page": page, "page_size": page_size, "total_pages": total_pages,
                "has_next": page < total_pages, "has_prev": page > 1, "data": items}

    def _apply_filters(self, filters: dict[str, Any]) -> tuple[list, Select]:
        """
        Returns conditions and query of stacked queries.
        """

        conditions = []
        query = select(self.model)

        if not filters:
            return conditions, query

        for key, value in filters.items():
            # Only add valid attributes
            if hasattr(self.model, key):
                conditions.append(getattr(self.model, key) == value)
        if conditions:
            query = query.where(and_(*conditions))

        return conditions, query

    async def _commit_with_handling(self, instance: ModelType | None = None) -> None:
        """
        Commits current state of commits and refreshes instance.
        If instance is None only commits.
        If there is duplicate of unique field, IntegrityError is called.
        """
        try:
            await self.db.commit()
        except (IntegrityError, HTTPException, Exception) as e:
            from app.core.logger import logger
            from app.db.models.company_model import Company

            logger.critical(e)

            raise RecordAlreadyExistsException()

        if instance:
            await self.db.refresh(instance)

    async def save_changes_and_refresh(self, instance: ModelType) -> None:
        """
        Wrapper for commit_with_handling() that also adds an instance to db.
        """

        self.db.add(instance)
        await self._commit_with_handling(instance=instance)

    async def get_instance_by_field_or_404(self, field_name: str, field_value: Any) -> ModelType:
        """
        Gets instance by field.
        If no instance exists, raise error.
        Else returns instance.
        """
        if not hasattr(self.model, field_name):
            raise InvalidSQLModelFieldNameException(field_name)

        # Assigned a specific type hint, so that ide won't show warning
        field: InstrumentedAttribute = getattr(self.model, field_name)

        result = await self.db.execute(select(self.model).where(field == field_value))

        instance = result.scalar_one_or_none()

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
        await self._commit_with_handling()
