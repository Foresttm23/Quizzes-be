import uuid
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any

from pydantic import BaseModel

from app.core.logger import logger
from app.db.repository.base_repository import BaseRepository

RepoType = TypeVar("RepoType", bound=BaseRepository)
SchemaType = TypeVar("SchemaType", bound=BaseModel)


class BaseService(ABC, Generic[RepoType]):
    @property
    @abstractmethod
    def display_name(self) -> str:
        pass

    def __init__(self, repo: RepoType):
        self.repo = repo

    async def fetch_instance(self, field_name: str, field_value: Any):
        """Method for getting an instance by field"""
        instance = await self.repo.get_instance_or_404(field_name=field_name, field_value=field_value)
        return instance

    async def fetch_instances_paginated(self, page: int, page_size: int):
        """Method for getting all instances paginated"""
        instances = await self.repo.get_instances_paginated(page=page, page_size=page_size)
        return instances

    async def _update_instance_by_id(self, instance_id: uuid.UUID, new_data: SchemaType):
        """
        Method for updating instance details by id.
        Should only be called inside subclasses
        with the specified Schema in parameters.
        """
        instance = await self.repo.get_instance_or_404(field_name="id", field_value=instance_id)

        changes = self.repo.apply_instance_updates(instance=instance, new_instance_info=new_data)

        # If not changes return instance from db
        if not changes:
            return instance

        await self.repo.save_changes_and_refresh(instance=instance)

        logger.info(f"{self.display_name}: {instance.id} updated")
        logger.debug(f"{self.display_name}: {instance.id} changes: {changes}")

        return instance

    async def delete_instance_by_id(self, instance_id: uuid.UUID) -> None:
        """Method for deleting an instance by id"""
        instance = await self.repo.get_instance_or_404(field_name="id", field_value=instance_id)

        logger.info(f"Deleted {self.display_name}: {instance.id}")

        await self.repo.delete_instance(instance=instance)
