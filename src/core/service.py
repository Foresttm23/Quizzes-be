from abc import ABC, abstractmethod
from uuid import UUID

from pydantic import BaseModel as BaseSchema

from .logger import logger
from .models import Base as BaseModel
from .repository import BaseRepository


class BaseService[R: BaseRepository, M: BaseModel](ABC):
    @property
    @abstractmethod
    def display_name(self) -> str:
        pass

    def __init__(self, repo: R):
        self.repo = repo

    def _update_instance(self, instance: M, new_data: BaseSchema, by: UUID) -> M:
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

    async def _delete_instance(self, instance: M) -> None:
        logger.info(f"Deleted {self.display_name}: {instance.id}")
        await self.repo.delete_instance(instance=instance)
