from datetime import datetime, timedelta, timezone
from typing import Sequence
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.sql.base import ExecutableOption

from core.utils import sanitize
from src.auth.repository import UserRepository
from src.auth.schemas import UserAverageSystemStatsResponseSchema
from src.company.schemas import UserAverageCompanyStatsResponseSchema
from src.company.service import MemberService
from src.core.caching.config import CacheConfig
from src.core.caching.keys import quiz_questions_and_options, quiz_time_limit_minutes, \
    user_stats_in_company, user_stats_system_wide
from src.core.caching.manager import CacheManager
from src.core.caching.rules import cache_attempt_if_finished
from src.core.exceptions import InstanceNotFoundException, ResourceConflictException
from src.core.logger import logger
from src.core.schemas import PaginationResponse
from src.core.service import BaseService
from .enums import AttemptStatus
from .models import AttemptAnswerSelection as AttemptAnswerSelectionModel
from .models import CompanyQuiz as CompanyQuizModel
from .models import CompanyQuizQuestion as CompanyQuizQuestionModel
from .models import QuestionAnswerOption as QuestionAnswerOptionModel
from .models import QuizAttempt as QuizAttemptModel
from .models import QuizAttemptAnswer as QuizAttemptAnswerModel
from .repository import AnswerRepository, AttemptRepository, QuestionRepository, QuizRepository
from .schemas import (AnswerOptionsCreateRequestSchema, CompanyQuizAdminSchema, CompanyQuizBaseSchema,
                      CompanyQuizQuestionAdminSchema, CompanyQuizSchema, QuestionAnswerOptionAdminSchema,
                      QuestionCreateRequestSchema, QuestionUpdateRequestSchema, QuizAttemptAdminAndQuizRelSchema,
                      QuizAttemptAdminSchema, QuizAttemptAnswerAdminSchema, QuizCreateRequestSchema,
                      QuizUpdateRequestSchema, SaveAnswerRequestSchema, CompanyQuizQuestionSchema,
                      QuizAttemptAndQuizRelSchema, QuizStartAttemptResponseSchema, QuizReviewAttemptResponseSchema,
                      QuizAttemptBaseSchema, )
from .utils.attempt_logic import assert_attempt_in_progress, get_finalize_attempt_options, get_attempt_details_options, \
    get_attempt_filters, get_active_attempt_filters, calc_correct_answers_count, calc_score, get_answer_filters
from .utils.quiz_logic import get_all_quiz_filters, get_visible_quiz_filters, get_all_quizzes_filters, \
    get_visible_quizzes_filters, validate_quiz, update_question_options, assert_valid_question


class QuizService(BaseService[QuizRepository]):
    @property
    def display_name(self) -> str:
        return "Quiz"

    def __init__(self, db: AsyncSession, cache_manager: CacheManager, member_service: MemberService):
        super().__init__(repo=QuizRepository(db=db), cache_manager=cache_manager)
        self.member_service = member_service
        self.question_repo = QuestionRepository(db=db)

    async def _get_quiz_model(self, company_id, quiz_id: UUID, is_admin: bool,
                              relationships: set[InstrumentedAttribute] | None = None,
                              options: Sequence[ExecutableOption] | None = None) -> CompanyQuizModel:
        if is_admin:
            filters = get_all_quiz_filters(company_id=company_id, quiz_id=quiz_id)

        else:
            filters = get_visible_quiz_filters(company_id=company_id, quiz_id=quiz_id)

        quiz = await self.repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships,
                                                               options=options)
        if not quiz:
            raise InstanceNotFoundException(instance_name=self.display_name)

        return quiz

    # TODO? caching when published
    async def get_quiz(self, company_id: UUID, quiz_id: UUID,
                       is_admin: bool) -> CompanyQuizAdminSchema | CompanyQuizSchema:
        relationships = {CompanyQuizModel.questions}
        quiz_model = await self._get_quiz_model(company_id=company_id, quiz_id=quiz_id, is_admin=is_admin,
                                                relationships=relationships, )

        return sanitize(data=quiz_model, schema=CompanyQuizSchema, admin_schema=CompanyQuizAdminSchema,
                        is_admin=is_admin)

    @CacheManager.cached(config=CacheConfig.QUIZ_TIME_LIMIT, schema=None)
    async def get_quiz_time_limit_minutes(self, company_id: UUID, quiz_id: UUID) -> int | None:
        time_limit_minutes = await self.repo.get_quiz_time_limit_minutes(company_id=company_id, quiz_id=quiz_id)
        return time_limit_minutes

    @CacheManager.cached(config=CacheConfig.QUIZ_QUESTIONS, schema=CompanyQuizQuestionAdminSchema)
    async def _get_questions_and_options_cached(self, company_id: UUID, quiz_id: UUID) -> Sequence[
        CompanyQuizQuestionAdminSchema]:
        questions = await self.question_repo.get_questions_with_options(company_id=company_id, quiz_id=quiz_id)
        return [CompanyQuizQuestionAdminSchema.model_validate(question) for question in questions]

    async def get_questions_and_options(self, company_id: UUID, quiz_id: UUID, is_admin: bool) -> Sequence[
                                                                                                      CompanyQuizQuestionAdminSchema] | \
                                                                                                  Sequence[
                                                                                                      CompanyQuizQuestionSchema]:
        questions = await self._get_questions_and_options_cached(company_id=company_id, quiz_id=quiz_id)

        return sanitize(data=questions, schema=CompanyQuizQuestionSchema, admin_schema=CompanyQuizQuestionAdminSchema,
                        is_admin=is_admin)

    async def get_quizzes_paginated(self, company_id: UUID, user_id: UUID | None, page: int, page_size: int) -> \
            PaginationResponse[CompanyQuizBaseSchema]:
        is_admin = False
        if user_id:
            is_admin = self.member_service.has_admin_permission(company_id=company_id, user_id=user_id)

        if is_admin:
            filters = get_all_quizzes_filters(company_id=company_id)
        else:
            filters = get_visible_quizzes_filters(company_id=company_id)

        return await self.repo.get_instances_paginated(page=page, page_size=page_size, filters=filters,
                                                       return_schema=CompanyQuizBaseSchema)

    async def create_quiz(self, company_id: UUID, acting_user_id: UUID,
                          quiz_info: QuizCreateRequestSchema, ) -> CompanyQuizAdminSchema:
        """
        Creates a new quiz such that the version = 1; In order to copy quiz use publish instead.
        :param company_id:
        :param acting_user_id:
        :param quiz_info:
        :return:
        """
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        quiz_data = quiz_info.model_dump()
        new_quiz = CompanyQuizModel(id=uuid4(), **quiz_data, company_id=company_id)

        await self.repo.save_and_refresh(new_quiz)
        logger.info(f"Created new quiz: {new_quiz.id} company {company_id} by {acting_user_id}")

        return CompanyQuizAdminSchema.model_validate(new_quiz)

    async def create_question(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID,
                              question_info: QuestionCreateRequestSchema, ) -> CompanyQuizQuestionAdminSchema:
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question_data = question_info.model_dump()
        question = CompanyQuizQuestionModel(id=uuid4(), quiz_id=quiz_id, **question_data)

        await self.repo.save_and_refresh(question)
        logger.info(f"Created new question: {question.id} quiz {quiz_id} by {acting_user_id}")

        await self.cache_manager.delete(
            quiz_questions_and_options(company_id=company_id, quiz_id=quiz_id))
        return CompanyQuizQuestionAdminSchema.model_validate(question)

    async def create_answer_options(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID, question_id: UUID,
                                    options_info: AnswerOptionsCreateRequestSchema, ) -> QuestionAnswerOptionAdminSchema:
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question = await self._get_question_model(company_id=company_id, quiz_id=quiz_id, question_id=question_id)

        options_data = options_info.model_dump()
        options = QuestionAnswerOptionModel(id=uuid4(), question_id=question_id, **options_data)
        question.options.append(options)

        await self.repo.save_and_refresh(options)
        logger.info(
            f"Created new options for question: {question_id} quiz {quiz_id} company {company_id} by {acting_user_id}")

        await self.cache_manager.delete(
            quiz_questions_and_options(company_id=company_id, quiz_id=quiz_id))
        return QuestionAnswerOptionAdminSchema.model_validate(options)

    async def _assert_quiz_not_published(self, company_id: UUID, quiz_id: UUID) -> None:
        is_published = await self.repo.get_publish_status(company_id=company_id, quiz_id=quiz_id)
        if is_published:
            raise ResourceConflictException(
                message="Quiz already published. Can't modify. Copy quiz or create a new one.")

    async def delete_quiz(self, company_id: UUID, quiz_id: UUID, acting_user_id: UUID) -> None:
        # Checks if the acting user is the owner, and gets the corresponding model
        await self.member_service.assert_owner_permissions(company_id=company_id, user_id=acting_user_id)
        quiz = await self._get_quiz_model(company_id=company_id, quiz_id=quiz_id, is_admin=True)
        await self.repo.delete_instance(quiz)
        logger.info(f"Deleted quiz: {quiz_id} company {company_id} by {acting_user_id}")

        await self.repo.commit()

    async def delete_question(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID, question_id: UUID, ) -> None:
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question = await self._get_question_model(company_id=company_id, quiz_id=quiz_id, question_id=question_id)
        await self.repo.delete_instance(question)
        logger.info(f"Deleted question: {question_id} quiz_id {quiz_id} company {company_id} by {acting_user_id}")

        await self.cache_manager.delete(
            quiz_questions_and_options(company_id=company_id, quiz_id=quiz_id))
        await self.repo.commit()

    async def create_new_version_within_company(self, company_id: UUID, acting_user_id: UUID,
                                                curr_quiz_id: UUID) -> CompanyQuizAdminSchema:
        """
        Creates a new quiz version within the company. New quiz fields are is_published=False and is_visible=False, so that Admins+ can update quiz contents.
        :param company_id:
        :param acting_user_id:
        :param curr_quiz_id:
        :return: Quiz
        """
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        options = [selectinload(CompanyQuizModel.questions).selectinload(CompanyQuizQuestionModel.options)]
        curr_quiz = await self._get_quiz_model(company_id=company_id, quiz_id=curr_quiz_id, options=options,
                                               is_admin=True)

        root_id = curr_quiz.root_quiz_id if curr_quiz.root_quiz_id else curr_quiz_id
        last_ver = await self.repo.get_last_version_number(company_id=company_id, root_id=root_id)
        new_quiz = CompanyQuizModel(id=uuid4(), company_id=curr_quiz.company_id, title=curr_quiz.title,
                                    description=curr_quiz.description, allowed_attempts=curr_quiz.allowed_attempts,
                                    is_published=False, is_visible=False, root_quiz_id=root_id, version=last_ver + 1, )

        for old_q in curr_quiz.questions:
            new_quiz.questions.append(old_q.clone())

        await self.repo.save_and_refresh(new_quiz)
        logger.info(
            f"Created new_quiz version: {new_quiz.version} new_quiz {new_quiz.id} old_quiz {curr_quiz.id} by {acting_user_id}")

        return CompanyQuizAdminSchema.model_validate(new_quiz)

    async def publish_quiz(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID) -> CompanyQuizAdminSchema:
        """
        Publish new versions and allows to republish(hide other versions and showcase only the specific one).
        :param company_id:
        :param acting_user_id:
        :param quiz_id:
        :return:
        """
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        options = [selectinload(CompanyQuizModel.questions).selectinload(CompanyQuizQuestionModel.options)]
        quiz = await self._get_quiz_model(company_id=company_id, is_admin=True, quiz_id=quiz_id, options=options, )
        validate_quiz(quiz=quiz)

        if quiz.root_quiz_id:
            await self.repo.hide_other_versions(company_id=company_id, root_id=quiz.root_quiz_id,
                                                exclude_quiz_id=quiz.id, )

        quiz.is_published = True
        quiz.is_visible = True

        await self.repo.save_and_refresh(quiz)
        logger.info(f"Published quiz: {quiz.id} version {quiz.version} by {acting_user_id}")

        quiz_questions_and_options_key = quiz_questions_and_options(company_id=company_id,
                                                                    quiz_id=quiz_id)
        get_quiz_time_limit_minutes_key = quiz_time_limit_minutes(company_id=company_id,
                                                                  quiz_id=quiz_id)
        await self.cache_manager.delete(quiz_questions_and_options_key, get_quiz_time_limit_minutes_key)

        return CompanyQuizAdminSchema.model_validate(quiz)

    async def update_quiz(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID,
                          quiz_info: QuizUpdateRequestSchema, ) -> CompanyQuizAdminSchema:
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        quiz = await self._get_quiz_model(company_id=company_id, is_admin=True, quiz_id=quiz_id)
        quiz = self._update_instance(instance=quiz, new_data=quiz_info, by=acting_user_id)

        await self.repo.save_and_refresh(quiz)
        logger.info(f"Updated {self.display_name}: {quiz.id} by {acting_user_id}")

        await self.cache_manager.delete(quiz_time_limit_minutes(company_id=company_id, quiz_id=quiz_id))
        return CompanyQuizAdminSchema.model_validate(quiz)

    async def update_question(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID, question_id: UUID,
                              question_info: QuestionUpdateRequestSchema, ) -> CompanyQuizQuestionAdminSchema:
        await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question = await self._get_question_model(company_id=company_id, quiz_id=quiz_id, question_id=question_id)
        if question_info.text is not None:
            question.text = question_info.text

        question = update_question_options(question=question, full_question_info=question_info)
        await self.repo.save_and_refresh(question)
        logger.info(f"Updated {self.display_name}: {quiz_id} question {question_id} by {acting_user_id}")

        await self.cache_manager.delete(
            quiz_questions_and_options(company_id=company_id, quiz_id=quiz_id))
        return CompanyQuizQuestionAdminSchema.model_validate(question)

    async def _get_question_model(self, company_id: UUID, quiz_id: UUID, question_id: UUID,
                                  relationship: InstrumentedAttribute | None = None) -> CompanyQuizQuestionModel:
        question = await self.question_repo.get_question_or_none(company_id=company_id, quiz_id=quiz_id,
                                                                 question_id=question_id, relationship=relationship)
        question = assert_valid_question(question=question)
        return question

    # TODO caching. Since isn't used for now, can skip
    async def get_question(self, company_id: UUID, quiz_id: UUID, question_id: UUID) -> CompanyQuizQuestionAdminSchema:
        question = await self._get_question_model(company_id=company_id, quiz_id=quiz_id, question_id=question_id,
                                                  relationship=CompanyQuizQuestionModel.options)
        return CompanyQuizQuestionAdminSchema.model_validate(question)

    async def get_quiz_allowed_attempts(self, company_id: UUID, quiz_id: UUID) -> int:
        allowed_attempts = await self.repo.get_quiz_allowed_attempts(company_id=company_id, quiz_id=quiz_id)
        if allowed_attempts is None:
            raise InstanceNotFoundException(instance_name="Quiz")
        return allowed_attempts


class AttemptService(BaseService[AttemptRepository]):
    @property
    def display_name(self) -> str:
        return "QuizAttempt"

    def __init__(self, db: AsyncSession, cache_manager: CacheManager, member_service: MemberService,
                 quiz_service: QuizService):
        super().__init__(repo=AttemptRepository(db=db), cache_manager=cache_manager)
        self.member_service = member_service
        self.quiz_service = quiz_service
        self.user_repo = UserRepository(db=db)
        self.answer_repo = AnswerRepository(db=db)
        self.question_repo = QuestionRepository(db=db)

    async def start_attempt(  # TODO? maybe fetch quiz directly and just verify its fields.
            self, company_id: UUID, quiz_id: UUID, user_id: UUID) -> tuple[
        Sequence[CompanyQuizQuestionAdminSchema], QuizAttemptAdminSchema]:
        await self.member_service.get_and_lock_member_row(company_id=company_id, user_id=user_id)

        existing_attempt_schema = await self._get_active_attempt_or_none(user_id=user_id, quiz_id=quiz_id)
        if existing_attempt_schema:
            questions_schema = await self.quiz_service.get_questions_and_options(company_id=company_id, quiz_id=quiz_id,
                                                                                 is_admin=False)
            return questions_schema, existing_attempt_schema

        await self._assert_user_have_attempts(company_id=company_id, quiz_id=quiz_id, user_id=user_id)

        time_limit_minutes = await self.quiz_service.get_quiz_time_limit_minutes(company_id=company_id, quiz_id=quiz_id)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=time_limit_minutes) if time_limit_minutes else None

        attempt = QuizAttemptModel(user_id=user_id, quiz_id=quiz_id, expires_at=expires_at)
        await self.repo.save_and_refresh(attempt)

        questions_schema = await self.quiz_service.get_questions_and_options(company_id=company_id, quiz_id=quiz_id,
                                                                             is_admin=False)
        attempt_schema = QuizAttemptAdminSchema.model_validate(attempt)

        return questions_schema, attempt_schema

    async def submit_attempt(self, user_id: UUID, attempt_id: UUID) -> QuizAttemptBaseSchema:
        options = get_finalize_attempt_options()
        attempt = await self._get_attempt_model(user_id=user_id, attempt_id=attempt_id, options=options)

        if attempt.status != AttemptStatus.IN_PROGRESS:  # Basic return if finished
            return QuizAttemptBaseSchema.model_validate(attempt)

        if attempt.is_expired():  # Expire
            attempt = await self._finalize_attempt(attempt=attempt, status=AttemptStatus.EXPIRED)
        else:
            attempt = await self._finalize_attempt(attempt=attempt, status=AttemptStatus.COMPLETED)  # Finish

        return QuizAttemptBaseSchema.model_validate(attempt)

    async def _finalize_attempt(self, attempt: QuizAttemptModel, status: AttemptStatus) -> QuizAttemptModel:
        """
        Update attempt fields to finnish the attempt. Grade existing answers, change status and set finished time.
        Expects loaded attempt.quiz, attempt.answers and attempt.options.
        Returns QuizAttemptModel, so external methods should validate themselves.
        """
        finished_time = datetime.now(timezone.utc)
        attempt = await self._finish_attempt_update_fields(attempt=attempt, finished_time=finished_time, status=status)

        await self.repo.save_and_refresh(attempt)
        logger.info(f"Finalized attempt: {attempt.id} status {attempt.status}")

        system_key = user_stats_system_wide(user_id=attempt.user_id)
        company_key = user_stats_in_company(company_id=attempt.quiz.company_id,
                                            acting_user_id=attempt.user_id,
                                            target_user_id=attempt.user_id)
        await self.cache_manager.delete(system_key, company_key)

        return attempt

    async def _finish_attempt_update_fields(self, attempt: QuizAttemptModel, finished_time: datetime,
                                            status: AttemptStatus) -> QuizAttemptModel:
        correct_count = calc_correct_answers_count(attempt)
        total_questions = await self.question_repo.get_questions_count_for_quiz(quiz_id=attempt.quiz_id)
        score = calc_score(correct_answers_count=correct_count, total_questions_count=total_questions)

        attempt.finished_at = finished_time
        attempt.score = score
        attempt.correct_answers_count = correct_count
        attempt.total_questions_count = total_questions
        attempt.status = status

        attempt.user.last_quiz_attempt_at = finished_time

        return attempt

    async def save_answer(self, user_id: UUID, question_id: UUID, attempt_id: UUID,
                          selected_option_info: SaveAnswerRequestSchema) -> QuizAttemptAnswerAdminSchema:
        attempt = await self._get_attempt_model(user_id=user_id, attempt_id=attempt_id)
        assert_attempt_in_progress(status=attempt.status, is_expired=attempt.is_expired())

        answer = await self._get_answer_model_or_none(question_id=question_id, attempt_id=attempt_id)
        if answer:
            answer.selected_options.clear()
        else:
            answer = QuizAttemptAnswerModel(attempt_id=attempt_id, question_id=question_id)

        for opt_id in selected_option_info.ids:
            answer_option = AttemptAnswerSelectionModel(option_id=opt_id)
            answer.selected_options.append(answer_option)

        await self.repo.save_and_refresh(answer)
        return QuizAttemptAnswerAdminSchema.model_validate(answer)

    async def _get_attempt_model(self, user_id: UUID, attempt_id: UUID,
                                 options: Sequence[ExecutableOption] | None = None, ) -> QuizAttemptModel:
        filters = get_attempt_filters(user_id=user_id, attempt_id=attempt_id)
        attempt = await self.repo.get_instance_by_filters_or_none(filters=filters, options=options)
        if attempt is None:
            raise InstanceNotFoundException(instance_name=self.display_name)
        return attempt

    async def _assert_user_have_attempts(self, company_id: UUID, quiz_id: UUID, user_id: UUID) -> None:
        allowed_attempts = await self.quiz_service.get_quiz_allowed_attempts(company_id=company_id, quiz_id=quiz_id)
        taken_attempts = await self.repo.get_user_attempts_count(company_id=company_id, user_id=user_id,
                                                                 quiz_id=quiz_id)
        if taken_attempts is None:
            raise InstanceNotFoundException(instance_name="Quiz")
        if taken_attempts >= allowed_attempts:
            raise ResourceConflictException("You have no attempts left for this quiz.")

    @CacheManager.cached(config=CacheConfig.ATTEMPT_DETAILS, schema=QuizAttemptAdminAndQuizRelSchema,
                         cache_condition=cache_attempt_if_finished)
    async def _get_attempt_details_cached(self, user_id: UUID, attempt_id: UUID) -> QuizAttemptAdminAndQuizRelSchema:
        options = get_attempt_details_options()
        attempt = await self._get_attempt_model(user_id=user_id, attempt_id=attempt_id, options=options)
        return QuizAttemptAdminAndQuizRelSchema.model_validate(attempt)

    async def get_attempt_details(self, user_id: UUID, attempt_id: UUID,
                                  is_admin: bool) -> QuizAttemptAdminAndQuizRelSchema | QuizAttemptAndQuizRelSchema:
        """Returns attempt with loaded answers and quiz relationships"""
        attempt_details = await self._get_attempt_details_cached(user_id=user_id, attempt_id=attempt_id)
        return sanitize(data=attempt_details, schema=QuizAttemptAndQuizRelSchema,
                        admin_schema=QuizAttemptAdminAndQuizRelSchema, is_admin=is_admin)

    async def get_attempt_results(self, user_id: UUID, attempt_id: UUID,
                                  is_admin: bool) -> QuizStartAttemptResponseSchema | QuizReviewAttemptResponseSchema:
        """Returns Admin schema if passed admin == True or the attempt ended. Else Basic with no correct option."""
        attempt = await self.get_attempt_details(user_id=user_id, attempt_id=attempt_id, is_admin=True)

        if attempt.status != AttemptStatus.IN_PROGRESS or attempt.is_expired or is_admin:
            questions = await self.quiz_service.get_questions_and_options(company_id=attempt.company_id,
                                                                          quiz_id=attempt.quiz_id, is_admin=True)
            return QuizReviewAttemptResponseSchema.model_validate({"attempt": attempt, "questions": questions})
        else:
            questions = await self.quiz_service.get_questions_and_options(company_id=attempt.company_id,
                                                                          quiz_id=attempt.quiz_id, is_admin=is_admin)
            return QuizStartAttemptResponseSchema.model_validate({"attempt": attempt, "questions": questions})

    # TODO? Caching
    async def _get_active_attempt_or_none(self, user_id: UUID, quiz_id: UUID) -> QuizAttemptAdminSchema | None:
        filters = get_active_attempt_filters(user_id=user_id, quiz_id=quiz_id)
        attempt = await self.repo.get_instance_by_filters_or_none(filters=filters)
        if attempt is None:
            return None
        return QuizAttemptAdminSchema.model_validate(attempt)

    async def _check_and_expire_attempt(self, attempt: QuizAttemptModel) -> None:
        """
        Checks if expired, if so marks it and calls self._finalize_attempt().
        Refetches the attempt to ensure the correct fields for _finalize_attempt() are present.
        For worker only, other methods should check expiration manually.
        """
        if attempt.status == AttemptStatus.IN_PROGRESS and attempt.is_expired():
            options = get_finalize_attempt_options()
            attempt = await self._get_attempt_model(user_id=attempt.user_id, attempt_id=attempt.id, options=options)
            await self._finalize_attempt(attempt=attempt, status=AttemptStatus.EXPIRED)

    async def _get_answer_model_or_none(self, question_id: UUID, attempt_id: UUID) -> QuizAttemptAnswerModel | None:
        filters = get_answer_filters(question_id=question_id, attempt_id=attempt_id)
        relationships = {QuizAttemptAnswerModel.selected_options}
        answer = await self.answer_repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships)
        return answer

    @CacheManager.cached(config=CacheConfig.USER_STATS, schema=UserAverageCompanyStatsResponseSchema)
    async def get_user_stats_in_company(self, company_id: UUID, acting_user_id: UUID,
                                        target_user_id: UUID) -> UserAverageCompanyStatsResponseSchema:
        """If user sees itself, target_user_id is the same as acting_user_id. If admin watches company member user_id then target_user_id is different."""
        if acting_user_id != target_user_id:
            await self.member_service.assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
            await self.member_service.assert_users_from_same_company(company_id, acting_user_id, target_user_id)

        correct_answers_count, total_questions_count = await self.repo.get_user_company_stats(company_id=company_id,
                                                                                              user_id=target_user_id)
        score = calc_score(correct_answers_count=correct_answers_count, total_questions_count=total_questions_count)
        return UserAverageCompanyStatsResponseSchema(score=score, total_correct_answers=correct_answers_count,
                                                     total_questions_answered=total_questions_count,
                                                     user_id=target_user_id, company_id=company_id, )

    @CacheManager.cached(config=CacheConfig.USER_STATS, schema=UserAverageSystemStatsResponseSchema)
    async def get_user_stats_system_wide(self, user_id: UUID) -> UserAverageSystemStatsResponseSchema:
        correct_answers_count, total_questions_count = await self.repo.get_user_system_stats(user_id=user_id)
        score = calc_score(correct_answers_count=correct_answers_count, total_questions_count=total_questions_count)
        return UserAverageSystemStatsResponseSchema(score=score, total_correct_answers=correct_answers_count,
                                                    total_questions_answered=total_questions_count, )

    # TODO WORKER TO AUTO END OLD ATTEMPTS
