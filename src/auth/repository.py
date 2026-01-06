from sqlalchemy.ext.asyncio import AsyncSession

from core.repository import BaseRepository
from .models import User as UserModel


class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=UserModel, db=db)
