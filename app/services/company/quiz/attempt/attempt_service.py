from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InstanceNotFoundException
from app.core.exceptions import ResourceConflictException
from app.db.models import AttemptAnswerSelection
from app.db.models import CompanyQuizQuestion as QuestionModel, QuizAttempt as AttemptModel, \
    QuizAttemptAnswer as AnswerModel, QuestionAnswerOption as AnswerOptionModel
from app.db.repository.company.quiz.attempt.attempt_repository import AttemptRepository
from app.schemas.company.quiz.attempt.answer_schema import SaveAnswerRequestSchema
from app.services.base_service import BaseService
from app.services.company.member_service import MemberService
from app.services.company.quiz.quiz_service import QuizService
from app.utils.enum_utils import AttemptStatus


class AttemptService(BaseService[AttemptRepository]):
    @property
    def display_name(self) -> str:
        return "QuizAttempt"

    def __init__(self, db: AsyncSession, member_service: MemberService, quiz_service: QuizService):
        super().__init__(repo=AttemptRepository(db=db))
        self.member_service = member_service
        self.quiz_service = quiz_service

    async def start_attempt(self, company_id: UUID, quiz_id: UUID, user_id: UUID) -> tuple[
        Sequence[QuestionModel], AttemptModel]:
        await self.member_service.get_and_lock_member_row(company_id=company_id, user_id=user_id)

        await self._assert_user_have_attempts(company_id=company_id, quiz_id=quiz_id, user_id=user_id)

        attempt = AttemptModel(user_id=user_id, quiz_id=quiz_id)
        questions = await self.quiz_service.get_questions_and_options(company_id=company_id, quiz_id=quiz_id)
        await self.repo.save_and_refresh(attempt)

        return questions, attempt

    async def end_attempt(self, user_id: UUID, quiz_id: UUID, attempt_id: UUID,
                          status: AttemptStatus = AttemptStatus.COMPLETED) -> AttemptModel:
        attempt = await self.get_attempt(user_id=user_id, quiz_id=quiz_id, attempt_id=attempt_id)
        attempt.finished_at = datetime.now(timezone.utc)
        attempt.score = self._calc_score(attempt)
        attempt.status = status

        await self.repo.save_and_refresh(attempt)
        return attempt

    async def save_answer(self, user_id: UUID, quiz_id: UUID, question_id: UUID, attempt_id: UUID,
                          selected_option_info: SaveAnswerRequestSchema) -> AnswerModel:
        await self._assert_attempt_is_correct(user_id=user_id, quiz_id=quiz_id, attempt_id=attempt_id)

        answer = await self.get_answer_or_none(question_id=question_id, attempt_id=attempt_id)
        if answer:
            answer.selected_options.clear()
        else:
            answer = AnswerModel(attempt_id=attempt_id, question_id=question_id)

        for opt_id in selected_option_info.ids:
            answer_option = AttemptAnswerSelection(option_id=opt_id)
            answer.selected_options.append(answer_option)

        await self.repo.save_and_refresh(answer)
        return answer

    async def _assert_user_have_attempts(self, company_id: UUID, quiz_id: UUID, user_id: UUID) -> None:
        allowed_attempts = await self.quiz_service.get_quiz_allowed_attempts(company_id=company_id, quiz_id=quiz_id)
        taken_attempts = await self.repo.get_user_attempts_count(company_id=company_id, user_id=user_id,
                                                                 quiz_id=quiz_id)
        if taken_attempts is None:
            raise InstanceNotFoundException(instance_name="Quiz")
        if taken_attempts >= allowed_attempts:
            raise ResourceConflictException("You have no attempts left for this quiz.")

    async def _assert_attempt_is_correct(self, user_id: UUID, quiz_id: UUID, attempt_id: UUID) -> None:
        attempt_id = await self.repo.get_attempt_id(user_id=user_id, quiz_id=quiz_id, attempt_id=attempt_id)
        if attempt_id is None:
            raise InstanceNotFoundException(instance_name=self.display_name)

    async def get_attempt(self, user_id: UUID, quiz_id: UUID, attempt_id: UUID) -> AttemptModel:
        filters = {AttemptModel.user_id: user_id, AttemptModel.quiz_id: quiz_id, AttemptModel.id: attempt_id}
        attempt = await self.repo.get_instance_by_filters_or_none(filters=filters)
        if attempt is None:
            raise InstanceNotFoundException(instance_name=self.display_name)
        return attempt

    async def get_answer_or_none(self, question_id: UUID, attempt_id: UUID) -> AnswerModel | None:
        filters = {AnswerModel.attempt_id: attempt_id, AnswerModel.question_id: question_id}
        relationships = {AnswerModel.selected_options}
        answer = await self.repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships)
        return answer

    @staticmethod
    def _calc_score(attempt: AttemptModel) -> float:
        score = 0.0
        for answer in attempt.answers:
            question: QuestionModel = answer.question
            selected_options: list[AnswerModel] = answer.selected_options
            q_options: list[AnswerOptionModel] = question.options

            selected_ids = {opt.id for opt in selected_options}
            correct_ids = {opt.id for opt in q_options if opt.is_correct}

            if selected_ids == correct_ids:
                score += question.points

        return score
