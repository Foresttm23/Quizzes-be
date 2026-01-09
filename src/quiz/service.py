from datetime import datetime, timedelta, timezone
from typing import Any, Sequence
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.sql.base import ExecutableOption

from src.auth.repository import UserRepository
from src.company.service import MemberService
from src.core.exceptions import (
    InstanceNotFoundException,
    ResourceConflictException,
)
from src.core.logger import logger
from src.core.schemas import PaginationResponse
from src.core.service import BaseService

from .enums import AttemptStatus
from .models import (
    AttemptAnswerSelection as AttemptAnswerSelectionModel,
)
from .models import (
    CompanyQuiz as CompanyQuizModel,
)
from .models import (
    CompanyQuizQuestion as CompanyQuizQuestionModel,
)
from .models import (
    QuestionAnswerOption as QuestionAnswerOptionModel,
)
from .models import (
    QuizAttempt as QuizAttemptModel,
)
from .models import (
    QuizAttemptAnswer as QuizAttemptAnswerModel,
)
from .repository import (
    AnswerRepository,
    AttemptRepository,
    QuestionRepository,
    QuizRepository,
)
from .schemas import (
    AnswerOptionsCreateRequestSchema,
    QuestionCreateRequestSchema,
    QuestionUpdateRequestSchema,
    QuizCreateRequestSchema,
    QuizUpdateRequestSchema,
    SaveAnswerRequestSchema,
)
from .utils import QuizUtils


class QuizService(BaseService[QuizRepository]):
    @property
    def display_name(self) -> str:
        return "Quiz"

    def __init__(self, db: AsyncSession, member_service: MemberService):
        super().__init__(repo=QuizRepository(db=db))
        self.member_service = member_service
        self.question_repo = QuestionRepository(db=db)
        self.quiz_utils = QuizUtils()

    async def get_quiz(
        self,
        company_id,
        user_id: UUID | None,
        quiz_id: UUID,
        relationships: set[InstrumentedAttribute] | None = None,
        options: Sequence[ExecutableOption] | None = None,
    ) -> CompanyQuizModel:
        is_admin = False
        if user_id:
            is_admin = self.member_service.has_admin_permission(company_id=company_id, user_id=user_id)

        if is_admin:
            quiz = await self._get_all_quiz(
                company_id=company_id,
                quiz_id=quiz_id,
                relationships=relationships,
                options=options,
            )
        else:
            quiz = await self._get_visible_quiz(
                company_id=company_id,
                quiz_id=quiz_id,
                relationships=relationships,
                options=options,
            )

        if not quiz:
            raise InstanceNotFoundException(instance_name=self.display_name)

        return quiz

    async def _get_visible_quiz(
        self,
        company_id: UUID,
        quiz_id: UUID,
        relationships: set[InstrumentedAttribute] | None = None,
        options: Sequence[ExecutableOption] | None = None,
    ) -> CompanyQuizModel | None:
        filters = self.quiz_utils.get_visible_quiz_filters(company_id=company_id, quiz_id=quiz_id)
        quiz = await self.repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships, options=options)
        return quiz

    async def _get_all_quiz(
        self,
        company_id: UUID,
        quiz_id: UUID,
        relationships: set[InstrumentedAttribute] | None = None,
        options: Sequence[ExecutableOption] | None = None,
    ) -> CompanyQuizModel | None:
        filters = self.quiz_utils.get_all_quiz_filters(company_id=company_id, quiz_id=quiz_id)
        quiz = await self.repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships, options=options)
        return quiz

    async def get_quizzes_paginated(
        self, company_id: UUID, user_id: UUID | None, page: int, page_size: int
    ) -> PaginationResponse[CompanyQuizModel]:
        is_admin = False
        if user_id:
            is_admin = self.member_service.has_admin_permission(company_id=company_id, user_id=user_id)

        if is_admin:
            return await self._get_all_quizzes_paginated(company_id=company_id, page=page, page_size=page_size)
        else:
            return await self._get_visible_quizzes_paginated(company_id=company_id, page=page, page_size=page_size)

    async def get_questions_and_options(self, company_id: UUID, quiz_id: UUID) -> Sequence[CompanyQuizQuestionModel]:
        questions = await self.question_repo.get_questions_for_quiz(company_id=company_id, quiz_id=quiz_id)
        return questions

    async def _get_visible_quizzes_paginated(self, company_id, page: int, page_size: int):
        filters = self._get_visible_quizzes_filters(company_id=company_id)
        return await self.repo.get_instances_paginated(page=page, page_size=page_size, filters=filters)

    async def _get_all_quizzes_paginated(self, company_id, page: int, page_size: int):
        filters = self._get_all_quizzes_filters(company_id=company_id)
        return await self.repo.get_instances_paginated(page=page, page_size=page_size, filters=filters)

    @classmethod
    def _get_visible_quizzes_filters(cls, company_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {
            CompanyQuizModel.company_id: company_id,
            CompanyQuizModel.is_visible: True,
            CompanyQuizModel.is_published: True,
        }
        return filters

    @classmethod
    def _get_all_quizzes_filters(cls, company_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {CompanyQuizModel.company_id: company_id}
        return filters

    async def create_quiz(
        self,
        company_id: UUID,
        acting_user_id: UUID,
        quiz_info: QuizCreateRequestSchema,
    ) -> CompanyQuizModel:
        """
        Creates a new quiz such that the version = 1; In order to copy quiz use publish instead.
        :param company_id:
        :param acting_user_id:
        :param quiz_info:
        :return:
        """
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        quiz_data = quiz_info.model_dump()
        new_quiz = CompanyQuizModel(id=uuid4(), **quiz_data)

        await self.repo.save_and_refresh(new_quiz)
        logger.info(f"Created new quiz: {new_quiz.id} company {company_id} by {acting_user_id}")

        return new_quiz

    async def create_question(
        self,
        company_id: UUID,
        acting_user_id: UUID,
        quiz_id: UUID,
        question_info: QuestionCreateRequestSchema,
    ) -> CompanyQuizQuestionModel:
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question_data = question_info.model_dump()
        question = CompanyQuizQuestionModel(id=uuid4(), quiz_id=quiz_id, **question_data)

        await self.repo.save_and_refresh(question)
        logger.info(f"Created new question: {question.id} quiz {quiz_id} by {acting_user_id}")

        return question

    async def create_answer_options(
        self,
        company_id: UUID,
        acting_user_id: UUID,
        quiz_id: UUID,
        question_id: UUID,
        options_info: AnswerOptionsCreateRequestSchema,
    ):
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question = await self.get_question(company_id=company_id, quiz_id=quiz_id, question_id=question_id)

        options_data = options_info.model_dump()
        options = QuestionAnswerOptionModel(id=uuid4(), question_id=question_id, **options_data)
        question.options.append(options)

        await self.repo.save_and_refresh(options)
        logger.info(f"Created new options for question: {question_id} quiz {quiz_id} company {company_id} by {acting_user_id}")

        return options

    async def _assert_quiz_not_published(self, company_id: UUID, quiz_id: UUID) -> None:
        is_published = await self.repo.get_publish_status(company_id=company_id, quiz_id=quiz_id)
        if is_published:
            raise ResourceConflictException(message="Quiz already published. Can't modify. Copy quiz or create a new one.")

    async def delete_quiz(self, company_id: UUID, quiz_id: UUID, acting_user_id: UUID) -> None:
        # Only owner can delete quizzes
        await self.member_service.assert_owner_permissions(company_id=company_id, user_id=acting_user_id)
        quiz = await self.get_quiz(company_id=company_id, user_id=acting_user_id, quiz_id=quiz_id)
        await self.repo.delete_instance(quiz)
        logger.info(f"Deleted quiz: {quiz_id} company {company_id} by {acting_user_id}")

        await self.repo.commit()

    async def delete_question(
        self,
        company_id: UUID,
        acting_user_id: UUID,
        quiz_id: UUID,
        question_id: UUID,
    ) -> None:
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question = await self.get_question(company_id=company_id, quiz_id=quiz_id, question_id=question_id)
        await self.repo.delete_instance(question)
        logger.info(f"Deleted question: {question_id} quiz_id {quiz_id} company {company_id} by {acting_user_id}")

        await self.repo.commit()

    async def create_new_version_within_company(self, company_id: UUID, acting_user_id: UUID, curr_quiz_id: UUID) -> CompanyQuizModel:
        """
        Creates a new quiz version within the company. New quiz fields are is_published=False and is_visible=False, so that Admins+ can update quiz contents.
        :param company_id:
        :param acting_user_id:
        :param curr_quiz_id:
        :return: Quiz
        """
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        options = [selectinload(CompanyQuizModel.questions).selectinload(CompanyQuizQuestionModel.options)]
        curr_quiz = await self.get_quiz(
            company_id=company_id,
            user_id=acting_user_id,
            quiz_id=curr_quiz_id,
            options=options,
        )

        root_id = curr_quiz.root_quiz_id if curr_quiz.root_quiz_id else curr_quiz_id
        last_ver = await self.repo.get_last_version_number(company_id=company_id, root_id=root_id)
        new_quiz = CompanyQuizModel(
            id=uuid4(),
            company_id=curr_quiz.company_id,
            title=curr_quiz.title,
            description=curr_quiz.description,
            allowed_attempts=curr_quiz.allowed_attempts,
            is_published=False,
            is_visible=False,
            root_quiz_id=root_id,
            version=last_ver + 1,
        )

        for old_q in curr_quiz.questions:
            new_quiz.questions.append(old_q.clone())

        await self.repo.save_and_refresh(new_quiz)
        logger.info(f"Created new_quiz version: {new_quiz.version} new_quiz {new_quiz.id} old_quiz {curr_quiz.id} by {acting_user_id}")

        return new_quiz

    async def publish_quiz(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID) -> CompanyQuizModel:
        """
        Publish new versions and allows to republish(hide other versions and showcase only the specific one).
        :param company_id:
        :param acting_user_id:
        :param quiz_id:
        :return:
        """
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        options = [selectinload(CompanyQuizModel.questions).selectinload(CompanyQuizQuestionModel.options)]
        quiz = await self.get_quiz(
            company_id=company_id,
            user_id=acting_user_id,
            quiz_id=quiz_id,
            options=options,
        )
        self.quiz_utils.validate_quiz(quiz=quiz)

        if quiz.root_quiz_id:
            await self.repo.hide_other_versions(
                company_id=company_id,
                root_id=quiz.root_quiz_id,
                exclude_quiz_id=quiz.id,
            )

        quiz.is_published = True
        quiz.is_visible = True

        await self.repo.save_and_refresh(quiz)
        logger.info(f"Published quiz: {quiz.id} version {quiz.version} by {acting_user_id}")

        return quiz

    async def update_quiz(
        self,
        company_id: UUID,
        acting_user_id: UUID,
        quiz_id: UUID,
        quiz_info: QuizUpdateRequestSchema,
    ) -> CompanyQuizModel:
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        quiz = await self.get_quiz(company_id=company_id, user_id=acting_user_id, quiz_id=quiz_id)
        quiz = self._update_instance(instance=quiz, new_data=quiz_info, by=acting_user_id)

        await self.repo.save_and_refresh(quiz)
        logger.info(f"Updated {self.display_name}: {quiz.id} by {acting_user_id}")

        return quiz

    async def update_question(
        self,
        company_id: UUID,
        acting_user_id: UUID,
        quiz_id: UUID,
        question_id: UUID,
        question_info: QuestionUpdateRequestSchema,
    ) -> CompanyQuizQuestionModel:
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question = await self.get_question(company_id=company_id, quiz_id=quiz_id, question_id=question_id)
        if question_info.text is not None:
            question.text = question_info.text

        question = self._update_question_options(question=question, full_question_info=question_info)
        await self.repo.save_and_refresh(question)
        logger.info(f"Updated {self.display_name}: {quiz_id} question {question_id} by {acting_user_id}")

        return question

    @staticmethod
    def _update_question_options(
        question: CompanyQuizQuestionModel,
        full_question_info: QuestionUpdateRequestSchema,
    ) -> CompanyQuizQuestionModel:
        if full_question_info.options is None:
            return question

        question.options.clear()
        for opt in full_question_info.options:
            new_opt = QuestionAnswerOptionModel(
                id=uuid4(),
                text=opt.text,
                is_correct=opt.is_correct,
                question_id=question.id,
            )
            question.options.append(new_opt)

        return question

    def get_question_from_quiz(self, quiz: CompanyQuizModel, question_id: UUID) -> CompanyQuizQuestionModel:
        # Warning can be inefficient if there are too many questions, but generally better than a separate query for the question
        question = next((q for q in quiz.questions if q.id == question_id), None)
        question = self.quiz_utils.assert_valid_question(question=question)
        return question

    async def get_question(self, company_id: UUID, quiz_id: UUID, question_id: UUID) -> CompanyQuizQuestionModel:
        question = await self.question_repo.get_question_or_none(company_id=company_id, quiz_id=quiz_id, question_id=question_id)
        question = self.quiz_utils.assert_valid_question(question=question)
        return question

    async def get_quiz_allowed_attempts(self, company_id: UUID, quiz_id: UUID) -> int:
        allowed_attempts = await self.repo.get_quiz_allowed_attempts(company_id=company_id, quiz_id=quiz_id)
        if allowed_attempts is None:
            raise InstanceNotFoundException(instance_name="Quiz")
        return allowed_attempts


class AttemptService(BaseService[AttemptRepository]):
    @property
    def display_name(self) -> str:
        return "QuizAttempt"

    def __init__(self, db: AsyncSession, member_service: MemberService, quiz_service: QuizService):
        super().__init__(repo=AttemptRepository(db=db))
        self.member_service = member_service
        self.quiz_service = quiz_service
        self.user_repo = UserRepository(db=db)
        self.answer_repo = AnswerRepository(db=db)
        self.question_repo = QuestionRepository(db=db)
        self.quiz_utils = QuizUtils()

    async def start_attempt(
        self, company_id: UUID, quiz_id: UUID, user_id: UUID
    ) -> tuple[Sequence[CompanyQuizQuestionModel], QuizAttemptModel]:
        await self.member_service.get_and_lock_member_row(company_id=company_id, user_id=user_id)

        await self._assert_user_have_attempts(company_id=company_id, quiz_id=quiz_id, user_id=user_id)

        # Get quiz to retrieve time_limit_minutes
        quiz = await self.quiz_service.get_quiz(company_id=company_id, user_id=user_id, quiz_id=quiz_id)

        # Calculate expiration time (default 24 hours = 1440 minutes)
        time_limit_minutes = quiz.time_limit_minutes if quiz.time_limit_minutes is not None else 1440
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=time_limit_minutes)

        attempt = QuizAttemptModel(user_id=user_id, quiz_id=quiz_id, expires_at=expires_at)
        questions = await self.quiz_service.get_questions_and_options(company_id=company_id, quiz_id=quiz_id)
        await self.repo.save_and_refresh(attempt)

        return questions, attempt

    async def end_attempt(
        self,
        user_id: UUID,
        attempt_id: UUID,
        status: AttemptStatus = AttemptStatus.COMPLETED,
    ) -> QuizAttemptModel:
        load_options = [
            selectinload(QuizAttemptModel.answers).options(
                selectinload(QuizAttemptAnswerModel.selected_options),
                selectinload(QuizAttemptAnswerModel.question).selectinload(CompanyQuizQuestionModel.options),
            )
        ]
        attempt = await self.get_attempt(user_id=user_id, attempt_id=attempt_id, options=load_options)
        self._assert_attempt_in_progress(status=attempt.status)

        return await self._finalize_attempt(attempt=attempt, status=status)

    async def _finalize_attempt(self, attempt: QuizAttemptModel, status: AttemptStatus) -> QuizAttemptModel:
        """
        Update attempt fields to finnish the attempt. Grade existing answers, change status and set finished time.
        Expects loaded attempt.answers and attempt.options.
        """
        correct_count = self.quiz_utils.calc_correct_answers_count(attempt)
        total_questions = await self.question_repo.get_questions_count_for_quiz(quiz_id=attempt.quiz_id)
        score = self.quiz_utils.calc_score(correct_answers_count=correct_count, total_questions_count=total_questions)

        finished_time = datetime.now(timezone.utc)
        attempt.finished_at = finished_time
        attempt.score = score
        attempt.correct_answers_count = correct_count
        attempt.total_questions_count = total_questions
        attempt.status = status

        await self.user_repo.update_last_quiz_attempt_time(user_id=attempt.user_id, new_time=finished_time)

        await self.repo.save_and_refresh(attempt)
        return attempt

    async def save_answer(
        self, user_id: UUID, question_id: UUID, attempt_id: UUID, selected_option_info: SaveAnswerRequestSchema
    ) -> QuizAttemptAnswerModel:
        attempt = await self.get_attempt(user_id=user_id, attempt_id=attempt_id)
        self._assert_attempt_in_progress(status=attempt.status)

        answer = await self._get_answer_or_none(question_id=question_id, attempt_id=attempt_id)
        if answer:
            answer.selected_options.clear()
        else:
            answer = QuizAttemptAnswerModel(attempt_id=attempt_id, question_id=question_id)

        for opt_id in selected_option_info.ids:
            answer_option = AttemptAnswerSelectionModel(option_id=opt_id)
            answer.selected_options.append(answer_option)

        await self.repo.save_and_refresh(answer)
        return answer

    def _assert_attempt_in_progress(self, status: AttemptStatus) -> None:
        if status != AttemptStatus.IN_PROGRESS:
            raise ResourceConflictException(message=f"Cannot save answer. Attempt is {status.value}")

    async def _assert_user_have_attempts(self, company_id: UUID, quiz_id: UUID, user_id: UUID) -> None:
        allowed_attempts = await self.quiz_service.get_quiz_allowed_attempts(company_id=company_id, quiz_id=quiz_id)
        taken_attempts = await self.repo.get_user_attempts_count(company_id=company_id, user_id=user_id, quiz_id=quiz_id)
        if taken_attempts is None:
            raise InstanceNotFoundException(instance_name="Quiz")
        if taken_attempts >= allowed_attempts:
            raise ResourceConflictException("You have no attempts left for this quiz.")

    async def _assert_attempt_is_correct(self, user_id: UUID, quiz_id: UUID) -> None:
        attempt_id = await self.repo.get_attempt_id(user_id=user_id, quiz_id=quiz_id)
        if attempt_id is None:
            raise InstanceNotFoundException(instance_name=self.display_name)

    async def get_attempt(
        self,
        user_id: UUID,
        attempt_id: UUID,
        options: Sequence[ExecutableOption] | None = None,
    ) -> QuizAttemptModel:
        attempt = await self._fetch_attempt(user_id=user_id, attempt_id=attempt_id, options=options)
        await self._check_and_expire_attempt(attempt=attempt)
        return attempt

    async def _fetch_attempt(
        self,
        user_id: UUID,
        attempt_id: UUID,
        options: Sequence[ExecutableOption] | None = None,
    ) -> QuizAttemptModel:
        filters = {QuizAttemptModel.user_id: user_id, QuizAttemptModel.id: attempt_id}
        attempt = await self.repo.get_instance_by_filters_or_none(filters=filters, options=options)
        if attempt is None:
            raise InstanceNotFoundException(instance_name=self.display_name)

        return attempt

    async def _check_and_expire_attempt(self, attempt: QuizAttemptModel) -> None:
        """Checks if expired, if so marks it and calls self._finalize_attempt(). Refetches the attempt to ensure the correct fields for _finalize_attempt() are present."""
        if attempt.status == AttemptStatus.IN_PROGRESS and attempt.is_expired():
            load_options = [
                selectinload(QuizAttemptModel.answers).options(
                    selectinload(QuizAttemptAnswerModel.selected_options),
                    selectinload(QuizAttemptAnswerModel.question).selectinload(CompanyQuizQuestionModel.options),
                )
            ]
            attempt = await self._fetch_attempt(user_id=attempt.user_id, attempt_id=attempt.id, options=load_options)
            await self._finalize_attempt(attempt=attempt, status=AttemptStatus.EXPIRED)

    async def _get_answer_or_none(self, question_id: UUID, attempt_id: UUID) -> QuizAttemptAnswerModel | None:
        filters = {QuizAttemptAnswerModel.attempt_id: attempt_id, QuizAttemptAnswerModel.question_id: question_id}
        relationships = {QuizAttemptAnswerModel.selected_options}
        answer = await self.answer_repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships)
        return answer

    async def get_user_stats_in_company(self, company_id: UUID, acting_user_id: UUID, target_user_id: UUID) -> dict[str, int | float]:
        """If user sees itself, target_user_id is the same as acting_user_id. If admin watches company member user_id then target_user_id is different."""
        if acting_user_id != target_user_id:
            await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
            await self.member_service.assert_users_from_same_company(company_id, acting_user_id, target_user_id)

        correct_answers_count, total_questions_count = await self.repo.get_user_company_stats(company_id=company_id, user_id=target_user_id)
        score = self.quiz_utils.calc_score(correct_answers_count=correct_answers_count, total_questions_count=total_questions_count)
        return {
            "score": score,
            "total_correct_answers": correct_answers_count,
            "total_questions_answered": total_questions_count,
        }

    async def get_user_average_score_system_wide(self, user_id: UUID) -> dict[str, int | float]:
        correct_answers_count, total_questions_count = await self.repo.get_user_system_stats(user_id=user_id)
        score = self.quiz_utils.calc_score(correct_answers_count=correct_answers_count, total_questions_count=total_questions_count)
        return {
            "score": score,
            "total_correct_answers": correct_answers_count,
            "total_questions_answered": total_questions_count,
        }

    # TODO WORKER TO AUTO END OLD ATTEMPTS
