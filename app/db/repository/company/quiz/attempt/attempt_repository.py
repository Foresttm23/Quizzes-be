from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company.quiz.attempt.attempt_model import Attempt as AttemptModel
from app.db.repository.base_repository import BaseRepository


class QuizAttemptRepository(BaseRepository[AttemptModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=AttemptModel, db=db)
