from typing import Type, TypeVar, Generic, Any, Sequence

from pydantic import BaseModel as BaseSchema
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.sql import Select, Update, Delete
from sqlalchemy.sql.base import ExecutableOption

from app.core.exceptions import RecordAlreadyExistsException
from app.db.postgres import Base as BaseModel
from app.schemas.base_schemas import PaginationResponse

ModelType = TypeVar("ModelType", bound=BaseModel)
SchemaType = TypeVar("SchemaType", bound=BaseSchema)

BaseQuery = Select | Update | Delete


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_instances_paginated(self, page: int, page_size: int,
                                      filters: dict[InstrumentedAttribute, Any] | None = None) -> PaginationResponse[
        SchemaType]:
        stmt = select(self.model)
        stmt = self._apply_filters(filters, stmt)
        stmt = stmt.order_by(self.model.id.desc())

        result = await self.paginate_query(stmt, page, page_size)
        return result

    async def paginate_query(self, stmt: Select, page: int, page_size: int) -> PaginationResponse[SchemaType]:
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
        for attr, value in filters.items():
            query = query.where(attr == value)

        return query

    async def save_and_refresh(self, *instances: Base) -> None:
        """
        Adds instances, commits and refreshes them.
        If there is duplicate of unique field, IntegrityError is called and session is rolled back.
        """
        self.db.add_all(instances)
        await self.commit()

        for instance in instances:
            await self.db.refresh(instance)

    async def commit(self) -> None:
        """
        Commits the current transaction.
        """
        try:
            await self.db.commit()
        except IntegrityError:
            raise RecordAlreadyExistsException()

    async def get_instance_by_field_or_none(self, field: InstrumentedAttribute, value: Any,
                                            relationships: set[InstrumentedAttribute] | None = None,
                                            options: ExecutableOption | None = None) -> ModelType | None:
        """
        Gets instance by single field.
        :param field:
        :param value:
        :param relationships:
        :param options:
        :return: instance | None
        """

        instance = await self.get_instance_by_filters_or_none(filters={field: value}, relationships=relationships,
                                                              options=options)
        return instance

    async def get_instance_by_filters_or_none(self, filters: dict[InstrumentedAttribute, Any],
                                              relationships: set[InstrumentedAttribute] | None = None,
                                              options: Sequence[ExecutableOption] | None = None) -> ModelType | None:
        """
        Gets instance by many field.
        :param filters: Executes the .where() DB query to the passed args
        :param relationships: Executes selectinload to find 1 layer relationships (Quiz->Questions)
        :param options: Executes selectinload to find 2 layer relationships (Quiz->Questions->Answers)
        :return: instance | None
        """
        query = select(self.model)

        for attr, value in filters.items():
            query = query.where(attr == value)

        if relationships:
            for rel in relationships:
                query = query.options(selectinload(rel))

        if options:
            query = query.options(selectinload(*options))

        instance = await self.db.scalar(query)
        return instance

    @staticmethod
    def apply_instance_updates(instance: ModelType, new_instance_info: SchemaType) -> dict:
        """
        Helper function for updating instance details and keeping track of changes.
        Takes instance and new_instance_info.
        """
        changes = {}

        update_data = new_instance_info.model_dump(exclude_unset=True)
        for attr, new_value in update_data.items():
            old_value = getattr(instance, attr)
            if old_value != new_value:
                changes[attr] = {"from": old_value, "to": new_value}
                setattr(instance, attr, new_value)

        return changes

    async def delete_instance(self, instance: BaseModel) -> None:
        """
        Function to delete instance and commit changes.
        """
        await self.db.delete(instance)
