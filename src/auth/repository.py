from datetime import datetime
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import BaseRepository
from .models import User as UserModel


class UserRepository(BaseRepository[UserModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=UserModel, db=db)

    async def update_last_quiz_attempt_time(self, user_id: UUID, new_time: datetime) -> None:
        query = update(UserModel).where(UserModel.id == user_id).values(last_quiz_attempt_at=new_time)
        await self.db.execute(query)
