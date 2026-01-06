from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import QuizAttempt as AttemptModel
from app.db.repository.base_repository import BaseRepository
from db.models import CompanyQuiz as QuizModel


class AttemptRepository(BaseRepository[AttemptModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=AttemptModel, db=db)

    async def get_user_attempts_count(self, company_id: UUID, user_id: UUID, quiz_id: UUID) -> int:
        """
        Get attempts count of user for a specific quiz. Asserts that quiz belongs to the company.
        """
        query = select(func.count(AttemptModel.id)).join(QuizModel).where(AttemptModel.quiz_id == quiz_id,
                                                                          AttemptModel.user_id == user_id,
                                                                          QuizModel.company_id == company_id)
        attempts_taken = await self.db.scalar(query)
        return attempts_taken

    async def get_attempt(self, user_id: UUID, attempt_id: UUID, quiz_id: UUID) -> AttemptModel:
        query = select(AttemptModel).where(AttemptModel.user_id == user_id, AttemptModel.quiz_id == quiz_id,
                                           AttemptModel.id == attempt_id)
        attempt = await self.db.scalar(query)
        return attempt

    async def get_attempt_id(self, user_id: UUID, quiz_id: UUID, attempt_id: UUID) -> AttemptModel | None:
        query = select(AttemptModel.id).where(AttemptModel.user_id == user_id, AttemptModel.quiz_id == quiz_id,
                                              AttemptModel.id == attempt_id)
        attempt_id = await self.db.scalar(query)
        return attempt_id
