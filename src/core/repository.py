from typing import Any, Sequence, Type

from pydantic import BaseModel as BaseSchema
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.sql import Delete, Select, Update
from sqlalchemy.sql.base import ExecutableOption

from .exceptions import RecordAlreadyExistsException
from .models import Base as BaseModel
from .schemas import PaginationResponse

type QueryType = Select[Any] | Update | Delete


class BaseRepository[M: BaseModel]:
    def __init__(self, model: Type[M], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_instances_paginated[S: BaseSchema](
        self,
        page: int,
        page_size: int,
        return_schema: Type[S],
        filters: dict[InstrumentedAttribute, Any] | None = None,
        order_rules: Sequence[Any] | None = None,
    ) -> PaginationResponse[S]:
        stmt = select(self.model)
        stmt = self._apply_filters(filters, stmt)

        if order_rules is None:
            order_rules = [self.model.id.desc()]
        stmt = stmt.order_by(*order_rules)

        result = await self.paginate_query(
            stmt=stmt, page=page, page_size=page_size, return_schema=return_schema
        )
        return result

    async def paginate_query[S: BaseSchema](
        self, stmt: Select, page: int, page_size: int, return_schema: Type[S]
    ) -> PaginationResponse[S]:
        count_query = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_query) or 0

        total_pages = (total + page_size - 1) // page_size

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.db.scalars(stmt)
        items = result.all()

        return PaginationResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            data=[return_schema.model_validate(item) for item in items],
        )

    @staticmethod
    def _apply_filters[Q: QueryType](
        filters: dict[InstrumentedAttribute, Any] | None, base_query: Q
    ) -> Q:
        """
        Returns conditions and query of stacked queries.
        """
        if not filters:
            return base_query

        query = base_query  # Solely for readability
        for attr, value in filters.items():
            query = query.where(attr == value)

        return query

    async def save(self, *instances: BaseModel) -> None:
        self.db.add_all(instances)
        await self.commit()

    async def commit(self) -> None:
        try:
            await self.db.flush()
            await self.db.commit()
        except IntegrityError:
            raise RecordAlreadyExistsException()

    async def get_instance_by_field_or_none(
        self,
        field: InstrumentedAttribute,
        value: Any,
        relationships: set[InstrumentedAttribute] | None = None,
    ) -> M | None:
        """
        Gets instance by a single field.
        :param field:
        :param value:
        :param relationships:
        :return: instance | None
        """

        instance = await self.get_instance_by_filters_or_none(
            filters={field: value}, relationships=relationships
        )
        return instance

    async def get_instance_by_filters_or_none(
        self,
        filters: dict[InstrumentedAttribute, Any],
        relationships: set[InstrumentedAttribute] | None = None,
        options: Sequence[ExecutableOption] | None = None,
    ) -> M | None:
        """
        Gets instance by many field. Applies .model_dump(exclude_unset=True)
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
            query = query.options(*options)

        instance = await self.db.scalar(query)
        return instance

    @staticmethod
    def apply_instance_updates[S: BaseSchema](
        instance: M, new_instance_info: S
    ) -> dict:
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
