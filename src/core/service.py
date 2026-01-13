from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel as BaseSchema

from .caching.manager import CacheManager
from .logger import logger
from .models import Base as BaseModel
from .repository import BaseRepository

RepoType = TypeVar("RepoType", bound=BaseRepository)
ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseService(ABC, Generic[RepoType]):
    @property
    @abstractmethod
    def display_name(self) -> str:
        pass

    def __init__(self, repo: RepoType, cache_manager: CacheManager | None):
        self.repo = repo
        # Name is static and corresponds to the caching manager name=cache_manager
        self.cache_manager = cache_manager

    def _update_instance(
            self, instance: ModelType, new_data: BaseSchema, by: UUID
    ) -> ModelType:
        """
        Method for updating instance details by id.
        Should only be called inside subclasses with the specified Schema in parameters.
        Applies .model_dump(exclude_unset=True)
        """
        changes = self.repo.apply_instance_updates(
            instance=instance, new_instance_info=new_data
        )
        # If no changes return instance from db
        if not changes:
            return instance

        logger.debug(
            f"To Update {self.display_name}: {instance.id} changes: {changes} by {by}"
        )
        return instance

    async def _delete_instance(self, instance: BaseModel) -> None:
        logger.info(f"Deleted {self.display_name}: {instance.id}")
        await self.repo.delete_instance(instance=instance)
