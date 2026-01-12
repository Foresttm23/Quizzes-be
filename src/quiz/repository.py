from typing import Sequence
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.repository import BaseRepository

from .enums import AttemptStatus
from .models import (
    CompanyQuiz as CompanyQuizModel,
)
from .models import (
    CompanyQuizQuestion as CompanyQuestionModel,
)
from .models import (
    QuizAttempt as QuizAttemptModel,
)
from .models import (
    QuizAttemptAnswer as QuizAttemptAnswerModel,
)


class QuizRepository(BaseRepository[CompanyQuizModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyQuizModel, db=db)

    async def get_last_version_number(self, company_id: UUID, root_id: UUID) -> int:
        query = select(func.max(CompanyQuizModel.version)).where(
            CompanyQuizModel.company_id == company_id,
            or_(CompanyQuizModel.root_quiz_id == root_id, CompanyQuizModel.id == root_id),
        )
        current_max = await self.db.scalar(query)
        return current_max or 0

    async def get_publish_status(self, company_id: UUID, quiz_id: UUID) -> bool | None:
        query = select(CompanyQuizModel.is_published).where(CompanyQuizModel.id == quiz_id, CompanyQuizModel.company_id == company_id)
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
        query = (
            update(CompanyQuizModel)
            .where(
                CompanyQuizModel.company_id == company_id,
                CompanyQuizModel.id != exclude_quiz_id,
                or_(CompanyQuizModel.root_quiz_id == root_id, CompanyQuizModel.id == root_id),
            )
            .values(is_visible=False)
        )
        await self.db.execute(query)

    async def get_quiz_allowed_attempts(self, company_id: UUID, quiz_id: UUID) -> int | None:
        query = select(CompanyQuizModel.allowed_attempts).where(
            CompanyQuizModel.company_id == company_id,
            CompanyQuizModel.id == quiz_id,
        )
        allowed_attempts = await self.db.scalar(query)
        return allowed_attempts


class QuestionRepository(BaseRepository[CompanyQuestionModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyQuestionModel, db=db)

    async def get_question_or_none(self, company_id: UUID, quiz_id: UUID, question_id: UUID) -> CompanyQuestionModel | None:
        query = (
            select(CompanyQuestionModel)
            .join(CompanyQuizModel, CompanyQuestionModel.quiz_id == CompanyQuizModel.id)
            .where(
                CompanyQuestionModel.id == question_id,
                CompanyQuizModel.id == quiz_id,
                CompanyQuizModel.company_id == company_id,
            )
        )

        question = await self.db.scalar(query)
        return question

    async def get_questions_for_quiz(self, company_id: UUID, quiz_id: UUID) -> Sequence[CompanyQuestionModel]:
        query = (
            select(CompanyQuestionModel)
            .join(CompanyQuizModel)
            .where(
                CompanyQuestionModel.quiz_id == quiz_id,
                CompanyQuizModel.company_id == company_id,
            )
            .options(selectinload(CompanyQuestionModel.options))
        )
        questions = await self.db.scalars(query)
        return questions.all()

    async def get_questions_count_for_quiz(self, quiz_id: UUID) -> int:
        """Since require only quiz_id field, must ensure its correct. Example: attempt.quiz_id - ensures it exists and correct."""
        query = select(func.count(CompanyQuestionModel.id)).join(CompanyQuizModel).where(CompanyQuestionModel.quiz_id == quiz_id)
        count = await self.db.scalar(query)
        return count or 0


class AttemptRepository(BaseRepository[QuizAttemptModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=QuizAttemptModel, db=db)

    async def get_user_attempts_count(self, company_id: UUID, user_id: UUID, quiz_id: UUID) -> int:
        """
        Get attempts count of user for a specific quiz. Asserts that quiz belongs to the company.
        """
        query = (
            select(func.count(QuizAttemptModel.id))
            .join(CompanyQuizModel)
            .where(
                QuizAttemptModel.quiz_id == quiz_id,
                QuizAttemptModel.user_id == user_id,
                CompanyQuizModel.company_id == company_id,
            )
        )
        attempts_taken = await self.db.scalar(query)
        return attempts_taken or 0

    async def get_attempt_id(self, user_id: UUID, quiz_id: UUID) -> UUID | None:
        query = select(QuizAttemptModel.id).where(
            QuizAttemptModel.user_id == user_id,
            QuizAttemptModel.quiz_id == quiz_id,
        )
        attempt_id = await self.db.scalar(query)
        return attempt_id

    async def get_user_company_stats(self, user_id: UUID, company_id: UUID) -> tuple[int, int]:
        """
        :returns: total_correct_answers, total_questions_answered
        """
        query = (
            select(func.sum(QuizAttemptModel.correct_answers_count), func.sum(QuizAttemptModel.total_questions_count))
            .join(CompanyQuizModel)
            .where(
                QuizAttemptModel.user_id == user_id,
                CompanyQuizModel.company_id == company_id,
                QuizAttemptModel.status.in_([AttemptStatus.COMPLETED, AttemptStatus.EXPIRED]),
            )
        )

        result = await self.db.execute(query)
        correct_answers_count, total_questions_count = result.one()

        return correct_answers_count or 0, total_questions_count or 0

    async def get_user_system_stats(self, user_id: UUID) -> tuple[int, int]:
        """
        :returns: total_correct_answers, total_questions_answered
        """
        query = (
            select(func.sum(QuizAttemptModel.correct_answers_count), func.sum(QuizAttemptModel.total_questions_count))
            .join(CompanyQuizModel)
            .where(
                QuizAttemptModel.user_id == user_id,
                QuizAttemptModel.status.in_([AttemptStatus.COMPLETED, AttemptStatus.EXPIRED]),
            )
        )
        result = await self.db.execute(query)
        correct_answers_count, total_questions_count = result.one()

        return correct_answers_count or 0, total_questions_count or 0


class AnswerRepository(BaseRepository[QuizAttemptAnswerModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=QuizAttemptAnswerModel, db=db)
