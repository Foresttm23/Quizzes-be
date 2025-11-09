import uuid
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any

from pydantic import BaseModel

from app.core.logger import logger
from app.db.postgres import Base
from app.db.repository.base_repository import BaseRepository

RepoType = TypeVar("RepoType", bound=BaseRepository)
SchemaType = TypeVar("SchemaType", bound=BaseModel)
ModelType = TypeVar("ModelType", bound=Base)


class BaseService(ABC, Generic[RepoType]):
    @property
    @abstractmethod
    def display_name(self) -> str:
        pass

    def __init__(self, repo: RepoType):
        self.repo = repo

    async def _fetch_instance(self, field_name: str, field_value: Any) -> ModelType:
        """Method for getting an instance by field"""
        instance = await self.repo.get_instance_by_field_or_404(field_name=field_name, field_value=field_value)
        return instance

    async def _fetch_instances_data_paginated(self, page: int, page_size: int) -> dict[..., list[ModelType]]:
        """Method for getting all instances paginated"""
        instances = await self.repo.get_instances_data_paginated(page=page, page_size=page_size)
        return instances

    async def _update_instance(self, instance: ModelType, new_data: SchemaType) -> ModelType:
        """
        Method for updating instance details by id.
        Should only be called inside subclasses
        with the specified Schema in parameters.
        """
        changes = self.repo.apply_instance_updates(instance=instance, new_instance_info=new_data)

        # If not changes return instance from db
        if not changes:
            return instance

        await self.repo.save_changes_and_refresh(instance=instance)

        # Since I made __repr__ in DB model for id
        logger.info(f"{self.display_name}: {instance} updated")
        logger.debug(f"{self.display_name}: {instance} changes: {changes}")

        return instance

    async def _delete_instance_by_id(self, instance_id: uuid.UUID) -> None:
        """Method for deleting an instance by id"""
        instance = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=instance_id)

        logger.info(f"Deleted {self.display_name}: {instance.id}")

        await self.repo.delete_instance(instance=instance)
