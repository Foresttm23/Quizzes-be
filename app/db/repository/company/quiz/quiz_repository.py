from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Question as QuestionModel
from app.db.models import Quiz as QuizModel
from app.db.repository.base_repository import BaseRepository


class CompanyQuizRepository(BaseRepository[QuizModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=QuizModel, db=db)

    async def get_last_version_number(self, company_id: UUID, root_id: UUID) -> int | None:
        query = select(func.max(QuizModel.version)).where(QuizModel.company_id == company_id,
                                                          or_(QuizModel.root_quiz_id == root_id,
                                                              QuizModel.id == root_id), )
        current_max = await self.db.scalar(query)
        return current_max

    async def get_publish_status(self, company_id: UUID, quiz_id: UUID) -> bool | None:
        query = select(QuizModel.is_published).where(QuizModel.id == quiz_id, QuizModel.company_id == company_id)
        is_published = await self.db.scalar(query)
        return is_published

    async def hide_other_versions(self, company_id: UUID, root_id: UUID, exclude_quiz_id: UUID) -> None:
        """
        Hides other versions of the quiz. is_visible = False. Does not affect is_published field.
        :param company_id:
        :param root_id:
        :param exclude_quiz_id:
        :return: None
        """
        query = (update(QuizModel).where(QuizModel.company_id == company_id, QuizModel.id != exclude_quiz_id,
                                         or_(QuizModel.root_quiz_id == root_id, QuizModel.id == root_id), ).values(
            is_visible=False))
        await self.db.execute(query)

    async def get_question_or_none(self, company_id, quiz_id: UUID, question_id: UUID) -> QuestionModel | None:
        query = (select(QuestionModel).join(QuizModel, QuestionModel.quiz_id == QuizModel.id).where(
            QuestionModel.id == question_id, QuizModel.id == quiz_id, QuizModel.company_id == company_id, ))

        question = await self.db.scalar(query)
        return question

    async def get_questions_and_options(self, company_id: UUID, quiz_id: UUID) -> Sequence[QuestionModel]:
        query = (select(QuestionModel).join(QuizModel).where(QuestionModel.quiz_id == quiz_id,
                                                             QuizModel.company_id == company_id).options(
            selectinload(QuestionModel.options)))
        questions = await self.db.scalars(query)
        return questions.all()

    async def get_questions_count(self, company_id: UUID, quiz_id: UUID) -> int:
        query = (select(func.count(QuestionModel.id)).join(QuizModel).where(QuestionModel.quiz_id == quiz_id,
                                                                            QuizModel.company_id == company_id))
        count = await self.db.scalar(query)
        return count
