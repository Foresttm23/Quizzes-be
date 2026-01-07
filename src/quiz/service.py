from datetime import datetime, timezone
from typing import Sequence, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.sql.base import ExecutableOption

from src.company.enums import CompanyRole
from src.company.service import MemberService
from src.core.exceptions import InstanceNotFoundException, ResourceConflictException
from src.core.logger import logger
from src.core.schemas import PaginationResponse
from src.core.service import BaseService
from .enums import AttemptStatus
from .models import AttemptAnswerSelection as AttemptAnswerSelectionModel, CompanyQuiz as QuizModel, \
    CompanyQuizQuestion as QuestionModel, QuizAttempt as AttemptModel, QuizAttemptAnswer as AnswerModel, \
    QuestionAnswerOption as AnswerOptionModel
from .repository import AttemptRepository, QuizRepository, AnswerRepository, QuestionRepository
from .schemas import AnswerOptionsCreateRequestSchema, SaveAnswerRequestSchema, QuestionUpdateRequestSchema, \
    QuestionCreateRequestSchema, QuizCreateRequestSchema, QuizUpdateRequestSchema
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

    async def get_quiz(self, company_id, user_id: UUID | None, quiz_id: UUID,
                       relationships: set[InstrumentedAttribute] | None = None,
                       options: Sequence[ExecutableOption] | None = None) -> QuizModel:
        is_admin = False
        if user_id:
            is_admin = self.has_admin_permission(company_id=company_id, user_id=user_id)

        if is_admin:
            quiz = await self._get_all_quiz(company_id=company_id, quiz_id=quiz_id, relationships=relationships,
                                            options=options)
        else:
            quiz = await self._get_visible_quiz(company_id=company_id, quiz_id=quiz_id, relationships=relationships,
                                                options=options)

        if not quiz:
            raise InstanceNotFoundException(instance_name=self.display_name)

        return quiz

    async def _get_visible_quiz(self, company_id: UUID, quiz_id: UUID,
                                relationships: set[InstrumentedAttribute] | None = None,
                                options: Sequence[ExecutableOption] | None = None) -> QuizModel:
        filters = self.quiz_utils.get_visible_quiz_filters(company_id=company_id, quiz_id=quiz_id)
        quiz = await self.repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships,
                                                               options=options)
        return quiz

    async def _get_all_quiz(self, company_id: UUID, quiz_id: UUID,
                            relationships: set[InstrumentedAttribute] | None = None,
                            options: Sequence[ExecutableOption] | None = None) -> QuizModel:
        filters = self.quiz_utils.get_all_quiz_filters(company_id=company_id, quiz_id=quiz_id)
        quiz = await self.repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships,
                                                               options=options)
        return quiz

    async def get_quizzes_paginated(self, company_id: UUID, user_id: UUID | None, page: int, page_size: int) -> \
            PaginationResponse[QuizModel]:
        is_admin = False
        if user_id:
            is_admin = self.has_admin_permission(company_id=company_id, user_id=user_id)

        if is_admin:
            return await self._get_all_quizzes_paginated(company_id=company_id, page=page, page_size=page_size)
        else:
            return await self._get_visible_quizzes_paginated(company_id=company_id, page=page, page_size=page_size)

    async def get_questions_and_options(self, company_id: UUID, quiz_id: UUID) -> Sequence[QuestionModel]:
        questions = await self.question_repo.get_all_for_quiz(company_id=company_id, quiz_id=quiz_id)
        return questions

    async def _get_visible_quizzes_paginated(self, company_id, page: int, page_size: int):
        filters = self._get_visible_quizzes_filters(company_id=company_id)
        return await self.repo.get_instances_paginated(page=page, page_size=page_size, filters=filters)

    async def _get_all_quizzes_paginated(self, company_id, page: int, page_size: int):
        filters = self._get_all_quizzes_filters(company_id=company_id)
        return await self.repo.get_instances_paginated(page=page, page_size=page_size, filters=filters)

    @classmethod
    def _get_visible_quizzes_filters(cls, company_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {QuizModel.company_id: company_id, QuizModel.is_visible: True, QuizModel.is_published: True, }
        return filters

    @classmethod
    def _get_all_quizzes_filters(cls, company_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {QuizModel.company_id: company_id}
        return filters

    async def create_quiz(self, company_id: UUID, acting_user_id: UUID,
                          quiz_info: QuizCreateRequestSchema) -> QuizModel:
        """
        Creates a new quiz such that the version = 1; In order to copy quiz use publish instead.
        :param company_id:
        :param acting_user_id:
        :param quiz_info:
        :return:
        """
        await self._assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        quiz_data = quiz_info.model_dump()
        new_quiz = QuizModel(id=uuid4(), **quiz_data)

        await self.repo.save_and_refresh(new_quiz)
        logger.info(f"Created new quiz: {new_quiz.id} company {company_id} by {acting_user_id}")

        return new_quiz

    async def create_question(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID,
                              question_info: QuestionCreateRequestSchema, ) -> QuestionModel:
        await self._assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question_data = question_info.model_dump()
        question = QuestionModel(id=uuid4(), quiz_id=quiz_id, **question_data)

        await self.repo.save_and_refresh(question)
        logger.info(f"Created new question: {question.id} quiz {quiz_id} by {acting_user_id}")

        return question

    async def create_answer_options(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID, question_id: UUID,
                                    options_info: AnswerOptionsCreateRequestSchema, ):
        await self._assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question = await self.get_question(company_id=company_id, quiz_id=quiz_id, question_id=question_id)

        options_data = options_info.model_dump()
        options = AnswerOptionModel(id=uuid4(), question_id=question_id, **options_data)
        question.options.append(options)

        await self.repo.save_and_refresh(options)
        logger.info(
            f"Created new options for question: {question_id} quiz {quiz_id} company {company_id} by {acting_user_id}")

        return options

    async def _assert_quiz_not_published(self, company_id: UUID, quiz_id: UUID) -> None:
        is_published = await self.repo.get_publish_status(company_id=company_id, quiz_id=quiz_id)
        if is_published:
            raise ResourceConflictException(
                message="Quiz already published. Can't modify. Copy quiz or create a new one.")

    async def delete_quiz(self, company_id: UUID, quiz_id: UUID, acting_user_id: UUID) -> None:
        # Only owner can delete quizzes
        await self._assert_owner_permissions(company_id=company_id, user_id=acting_user_id)
        quiz = await self.get_quiz(company_id=company_id, user_id=acting_user_id, quiz_id=quiz_id)
        await self.repo.delete_instance(quiz)
        logger.info(f"Deleted quiz: {quiz_id} company {company_id} by {acting_user_id}")

        await self.repo.commit()

    async def delete_question(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID, question_id: UUID) -> None:
        await self._assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question = await self.get_question(company_id=company_id, quiz_id=quiz_id, question_id=question_id)
        await self.repo.delete_instance(question)
        logger.info(f"Deleted question: {question_id} quiz_id {quiz_id} company {company_id} by {acting_user_id}")

        await self.repo.commit()

    async def create_new_version_within_company(self, company_id: UUID, acting_user_id: UUID,
                                                curr_quiz_id: UUID) -> QuizModel:
        """
        Creates a new quiz version within the company. New quiz fields are is_published=False and is_visible=False, so that Admins+ can update quiz contents.
        :param company_id:
        :param acting_user_id:
        :param curr_quiz_id:
        :return: Quiz
        """
        await self._assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        options = [selectinload(QuizModel.questions).selectinload(QuestionModel.options)]
        curr_quiz = await self.get_quiz(company_id=company_id, user_id=acting_user_id, quiz_id=curr_quiz_id,
                                        options=options)

        root_id = curr_quiz.root_quiz_id if curr_quiz.root_quiz_id else curr_quiz_id
        last_ver = await self.repo.get_last_version_number(company_id=company_id, root_id=root_id)
        new_quiz = QuizModel(id=uuid4(), company_id=curr_quiz.company_id, title=curr_quiz.title,
                             description=curr_quiz.description, allowed_attempts=curr_quiz.allowed_attempts,
                             is_published=False, is_visible=False, root_quiz_id=root_id, version=last_ver + 1)

        for old_q in curr_quiz.questions:
            new_quiz.questions.append(old_q.clone())

        await self.repo.save_and_refresh(new_quiz)
        logger.info(
            f"Created new_quiz version: {new_quiz.version} new_quiz {new_quiz.id} old_quiz {curr_quiz.id} by {acting_user_id}")

        return new_quiz

    async def publish_quiz(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID) -> QuizModel:
        """
        Publish new versions and allows to republish(hide other versions and showcase only the specific one).
        :param company_id:
        :param acting_user_id:
        :param quiz_id:
        :return:
        """
        await self._assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        options = [selectinload(QuizModel.questions).selectinload(QuestionModel.options)]
        quiz = await self.get_quiz(company_id=company_id, user_id=acting_user_id, quiz_id=quiz_id, options=options)
        self.quiz_utils.validate_quiz(quiz=quiz)

        if quiz.root_quiz_id:
            await self.repo.hide_other_versions(company_id=company_id, root_id=quiz.root_quiz_id,
                                                exclude_quiz_id=quiz.id, )

        quiz.is_published = True
        quiz.is_visible = True

        await self.repo.save_and_refresh(quiz)
        logger.info(f"Published quiz: {quiz.id} version {quiz.version} by {acting_user_id}")

        return quiz

    async def update_quiz(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID,
                          quiz_info: QuizUpdateRequestSchema) -> QuizModel:
        await self._assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        quiz = await self.get_quiz(company_id=company_id, user_id=acting_user_id, quiz_id=quiz_id)
        quiz = self._update_instance(instance=quiz, new_data=quiz_info, by=acting_user_id)

        await self.repo.save_and_refresh(quiz)
        logger.info(f"Updated {self.display_name}: {quiz.id} by {acting_user_id}")

        return quiz

    async def update_question(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID, question_id: UUID,
                              question_info: QuestionUpdateRequestSchema) -> QuestionModel:
        await self._assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question = await self.get_question(company_id=company_id, quiz_id=quiz_id, question_id=question_id)
        question.text = question_info.text

        if question_info.options is not None:
            question = self._update_question_options(question=question, full_question_info=question_info)

        await self.repo.save_and_refresh(question)
        logger.info(f"Updated {self.display_name}: {quiz_id} question {question_id} by {acting_user_id}")

        return question

    @staticmethod
    def _update_question_options(question: QuestionModel,
                                 full_question_info: QuestionUpdateRequestSchema) -> QuestionModel:
        question.options.clear()
        for opt in full_question_info.options:
            new_opt = AnswerOptionModel(id=uuid4(), text=opt.text, is_correct=opt.is_correct, question_id=question.id, )
            question.options.append(new_opt)

        return question

    def get_question_from_quiz(self, quiz: QuizModel, question_id: UUID) -> QuestionModel:
        # Warning can be inefficient if there are too many questions, but generally better than a separate query for the question
        question = next((q for q in quiz.questions if q.id == question_id), None)
        self._assert_valid_question(question=question)
        return question

    async def get_question(self, company_id: UUID, quiz_id: UUID, question_id: UUID) -> QuestionModel:
        question = await self.question_repo.get_question_or_none(company_id=company_id, quiz_id=quiz_id,
                                                                 question_id=question_id)
        self._assert_valid_question(question=question)
        return question

    @staticmethod
    def _assert_valid_question(question: QuestionModel) -> None:
        if not question:
            raise InstanceNotFoundException(instance_name="Question")

    async def _assert_admin_permissions(self, company_id: UUID, user_id: UUID) -> None:
        await self.member_service.assert_user_permissions(company_id=company_id, user_id=user_id,
                                                          required_role=CompanyRole.ADMIN)

    async def _assert_owner_permissions(self, company_id: UUID, user_id: UUID) -> None:
        await self.member_service.assert_user_permissions(company_id=company_id, user_id=user_id,
                                                          required_role=CompanyRole.OWNER)

    async def has_admin_permission(self, company_id: UUID, user_id: UUID) -> bool:
        """
        :param company_id:
        :param user_id:
        :return: True if admin, False otherwise.
        """
        return await self.member_service.has_user_permissions(company_id=company_id, user_id=user_id,
                                                              required_role=CompanyRole.ADMIN)

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
        self.answer_repo = AnswerRepository(db=db)
        self.quiz_utils = QuizUtils()

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
        load_options = [selectinload(AttemptModel.answers).options(selectinload(AnswerModel.selected_options),
                                                                   selectinload(AnswerModel.question).selectinload(
                                                                       QuestionModel.options))]
        attempt = await self._get_attempt(user_id=user_id, quiz_id=quiz_id, attempt_id=attempt_id, options=load_options)

        attempt.finished_at = datetime.now(timezone.utc)
        attempt.score = self.quiz_utils.calc_score(attempt)
        attempt.status = status

        await self.repo.save_and_refresh(attempt)
        return attempt

    async def save_answer(self, user_id: UUID, quiz_id: UUID, question_id: UUID, attempt_id: UUID,
                          selected_option_info: SaveAnswerRequestSchema) -> AnswerModel:
        await self._assert_attempt_is_correct(user_id=user_id, quiz_id=quiz_id, attempt_id=attempt_id)

        answer = await self._get_answer_or_none(question_id=question_id, attempt_id=attempt_id)
        if answer:
            answer.selected_options.clear()
        else:
            answer = AnswerModel(attempt_id=attempt_id, question_id=question_id)

        for opt_id in selected_option_info.ids:
            answer_option = AttemptAnswerSelectionModel(option_id=opt_id)
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

    async def _get_attempt(self, user_id: UUID, quiz_id: UUID, attempt_id: UUID,
                           options: Sequence[ExecutableOption] | None = None) -> AttemptModel:
        filters = {AttemptModel.user_id: user_id, AttemptModel.quiz_id: quiz_id, AttemptModel.id: attempt_id}
        attempt = await self.repo.get_instance_by_filters_or_none(filters=filters, options=options)
        if attempt is None:
            raise InstanceNotFoundException(instance_name=self.display_name)
        return attempt

    async def _get_answer_or_none(self, question_id: UUID, attempt_id: UUID) -> AnswerModel | None:
        filters = {AnswerModel.attempt_id: attempt_id, AnswerModel.question_id: question_id}
        relationships = {AnswerModel.selected_options}
        answer = await self.answer_repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships)
        return answer

    # TODO WORKER TO AUTO END OLD ATTEMPTS
