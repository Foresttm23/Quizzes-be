from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from uuid import UUID

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

    def _update_instance(self, instance: ModelType, new_data: SchemaType, by: UUID) -> ModelType:
        """
        Method for updating instance details by id.
        Should only be called inside subclasses
        with the specified Schema in parameters.
        """
        changes = self.repo.apply_instance_updates(instance=instance, new_instance_info=new_data)
        # If no changes return instance from db
        if not changes:
            return instance

        logger.debug(f"To Update {self.display_name}: {instance.id} changes: {changes} by {by}")
        return instance

    async def _delete_instance(self, instance: ModelType) -> None:
        logger.info(f"Deleted {self.display_name}: {instance.id}")
        await self.repo.delete_instance(instance=instance)
