from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository.base_repository import BaseRepository
from db.models.user_model import User as UserModel


class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=UserModel, db=db)
