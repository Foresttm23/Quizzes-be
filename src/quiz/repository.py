from typing import Sequence
from uuid import UUID

from sqlalchemy import select, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.repository import BaseRepository
from .models import QuizAttempt as QuizAttemptModel, CompanyQuizQuestion as CompanyQuestionModel, \
    CompanyQuiz as QuizModel, QuestionAnswerOption as QuestionAnswerOptionModel


class QuizRepository(BaseRepository[QuizModel]):
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
                                         or_(QuizModel.root_quiz_id == root_id, QuizModel.id == root_id)).values(
            is_visible=False))
        await self.db.execute(query)

    async def get_quiz_allowed_attempts(self, company_id: UUID, quiz_id: UUID) -> int | None:
        query = select(QuizModel.allowed_attempts).where(QuizModel.company_id == company_id, QuizModel.id == quiz_id, )
        allowed_attempts = await self.db.scalar(query)
        return allowed_attempts


class QuestionRepository(BaseRepository[CompanyQuestionModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyQuestionModel, db=db)

    async def get_question_or_none(self, company_id: UUID, quiz_id: UUID,
                                   question_id: UUID) -> CompanyQuestionModel | None:
        query = (select(CompanyQuestionModel).join(QuizModel, CompanyQuestionModel.quiz_id == QuizModel.id).where(
            CompanyQuestionModel.id == question_id, QuizModel.id == quiz_id, QuizModel.company_id == company_id, ))

        question = await self.db.scalar(query)
        return question

    async def get_all_for_quiz(self, company_id: UUID, quiz_id: UUID) -> Sequence[CompanyQuestionModel]:
        query = (select(CompanyQuestionModel).join(QuizModel).where(CompanyQuestionModel.quiz_id == quiz_id,
                                                                    QuizModel.company_id == company_id).options(
            selectinload(CompanyQuestionModel.options)))
        questions = await self.db.scalars(query)
        return questions.all()

    async def get_count_for_quiz(self, company_id: UUID, quiz_id: UUID) -> int | None:
        query = (
            select(func.count(CompanyQuestionModel.id)).join(QuizModel).where(CompanyQuestionModel.quiz_id == quiz_id,
                                                                              QuizModel.company_id == company_id))
        count = await self.db.scalar(query)
        return count


class AttemptRepository(BaseRepository[QuizAttemptModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=QuizAttemptModel, db=db)

    async def get_user_attempts_count(self, company_id: UUID, user_id: UUID, quiz_id: UUID) -> int:
        """
        Get attempts count of user for a specific quiz. Asserts that quiz belongs to the company.
        """
        query = select(func.count(QuizAttemptModel.id)).join(QuizModel).where(QuizAttemptModel.quiz_id == quiz_id,
                                                                              QuizAttemptModel.user_id == user_id,
                                                                              QuizModel.company_id == company_id)
        attempts_taken = await self.db.scalar(query)
        return attempts_taken

    async def get_attempt_id(self, user_id: UUID, quiz_id: UUID, attempt_id: UUID) -> UUID | None:
        query = select(QuizAttemptModel.id).where(QuizAttemptModel.user_id == user_id,
                                                  QuizAttemptModel.quiz_id == quiz_id,
                                                  QuizAttemptModel.id == attempt_id)
        attempt_id = await self.db.scalar(query)
        return attempt_id


class AnswerRepository(BaseRepository[QuestionAnswerOptionModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=QuestionAnswerOptionModel, db=db)
