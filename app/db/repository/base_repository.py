from http.client import HTTPException
from typing import Type, TypeVar, Generic, Any

from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql import Select, Update, Delete

from app.core.exceptions import RecordAlreadyExistsException, InstanceNotFoundException
from app.db.postgres import Base
from schemas.base_schemas import PaginationResponse

ModelType = TypeVar("ModelType", bound=Base)
SchemaType = TypeVar("SchemaType", bound=BaseModel)

BaseQuery = Select | Update | Delete


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_instances_data_paginated(self, page: int, page_size: int,
                                           filters: dict[InstrumentedAttribute, Any] | None = None) -> \
            PaginationResponse[ModelType]:
        stmt = select(self.model)
        stmt = self._apply_filters(filters, stmt)
        stmt = stmt.order_by(self.model.id.desc())

        result = await self.paginate_query(stmt, page, page_size)
        return result

    async def paginate_query(self, stmt: Select, page: int, page_size: int) -> PaginationResponse[ModelType]:
        count_query = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_query) or 0

        total_pages = (total + page_size - 1) // page_size

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.db.scalars(stmt)
        items = result.all()

        return PaginationResponse(total=total, page=page, page_size=page_size, total_pages=total_pages,
                                  has_next=page < total_pages, has_prev=page > 1, data=items)

    @staticmethod
    def _apply_filters(filters: dict[InstrumentedAttribute, Any], base_query: BaseQuery) -> BaseQuery:
        """
        Returns conditions and query of stacked queries.
        """
        if not filters:
            return base_query

        query = base_query  # Solely for readability
        for key, value in filters.items():
            query = query.where(key == value)

        return query

    async def _commit_with_handling(self, *args: Base) -> None:
        """
        Commits current state of commits and refreshes instances.
        If *args is None only commits.
        If there is duplicate of unique field, IntegrityError is called and session is rolled back.
        """
        try:
            await self.db.commit()
        except (IntegrityError, HTTPException) as e:
            raise RecordAlreadyExistsException()

        for instance in args:
            await self.db.refresh(instance)

    async def save_changes_and_refresh(self, *args: Base) -> None:
        """
        Wrapper for commit_with_handling() that also adds an instance to db.
        """
        self.db.add_all(args)
        await self._commit_with_handling(*args)

    async def get_instance_by_field_or_404(self, field: InstrumentedAttribute, value: Any) -> ModelType:
        """
        Gets instance by field.
        If no instance exists, raise error.
        Else returns instance.
        """
        query = select(self.model).where(field == value)

        instance = await self.db.scalar(query)
        if instance is None:
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
