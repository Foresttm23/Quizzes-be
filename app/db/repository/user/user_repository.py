from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user.user_model import User as UserModel
from app.db.repository.base_repository import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=UserModel, db=db)
