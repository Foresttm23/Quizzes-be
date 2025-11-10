from pydantic import BaseModel, EmailStr

from app.db.repository.base_repository import BaseRepository
from app.services.base_service import BaseService, ModelType


class _TestCreateSchema(BaseModel):
    email: EmailStr
    username: str


class _TestUpdateSchema(BaseModel):
    username: str | None = None
    email: EmailStr | None = None


class _TestUserRepository(BaseRepository):
    pass


class _TestService(BaseService[_TestUserRepository]):
    @property
    def display_name(self) -> str:
        return "Test Model"

    async def helper_create_instance(self, data: _TestCreateSchema) -> ModelType:
        """A helper/wrapper function for save_changes_and_refresh"""
        instance = self.repo.model(**data.model_dump())
        await self.repo.save_changes_and_refresh(instance=instance)
        return instance
