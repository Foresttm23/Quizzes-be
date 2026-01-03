from typing import Sequence, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.sql.base import ExecutableOption

from app.core.exceptions import InstanceNotFoundException
from app.core.exceptions import ResourceConflictException
from app.core.logger import logger
from app.db.models import AnswerOption as AnswerOptionModel
from app.db.models import Question as QuestionModel
from app.db.models import Quiz as QuizModel
from app.db.repository.company.quiz.quiz_repository import CompanyQuizRepository
from app.schemas.base_schemas import PaginationResponse
from app.schemas.company.quiz.answer_option_schema import AnswerOptionsCreateRequestSchema
from app.schemas.company.quiz.question_schema import (QuestionUpdateRequestSchema, QuestionCreateRequestSchema, )
from app.schemas.company.quiz.quiz_schema import (QuizCreateRequestSchema, QuizUpdateRequestSchema, )
from app.services.base_service import BaseService
from app.services.company.member_service import CompanyMemberService
from app.utils.enum_utils import CompanyRole


class QuizService(BaseService[CompanyQuizRepository]):
    @property
    def display_name(self) -> str:
        return "Quiz"

    def __init__(self, db: AsyncSession, company_member_service: CompanyMemberService):
        super().__init__(repo=CompanyQuizRepository(db=db))
        self.company_member_service = company_member_service

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
        filters = self._get_visible_quiz_filters(company_id=company_id, quiz_id=quiz_id)
        quiz = await self.repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships,
                                                               options=options)
        return quiz

    async def _get_all_quiz(self, company_id: UUID, quiz_id: UUID,
                            relationships: set[InstrumentedAttribute] | None = None,
                            options: Sequence[ExecutableOption] | None = None) -> QuizModel:
        filters = self._get_all_quiz_filters(company_id=company_id, quiz_id=quiz_id)
        quiz = await self.repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships,
                                                               options=options)
        return quiz

    @classmethod
    def _get_visible_quiz_filters(cls, company_id: UUID, quiz_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {QuizModel.company_id: company_id, QuizModel.id: quiz_id, QuizModel.is_published: True,
                   QuizModel.is_visible: True, }
        return filters

    @classmethod
    def _get_all_quiz_filters(cls, company_id: UUID, quiz_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {QuizModel.company_id: company_id, QuizModel.id: quiz_id}
        return filters

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
        questions = await self.repo.get_questions_and_options(company_id=company_id, quiz_id=quiz_id)
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
        quiz = await self.get_quiz(company_id=company_id, quiz_id=quiz_id)
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
        curr_quiz = await self.get_quiz(company_id=company_id, quiz_id=curr_quiz_id, options=options)

        root_id = curr_quiz.root_quiz_id if curr_quiz.root_quiz_id else curr_quiz_id
        last_ver = await self.repo.get_last_version_number(company_id=company_id, root_id=root_id)
        new_quiz = QuizModel(id=uuid4(), company_id=curr_quiz.company_id, title=curr_quiz.title,
                             description=curr_quiz.description, allowed_attempts=curr_quiz.allowed_attempts,
                             is_published=False, is_visible=False, root_quiz_id=root_id, version=last_ver + 1, )

        for old_q in curr_quiz.questions:
            new_quiz.questions.append(old_q.clone())

        await self.repo.save_and_refresh(new_quiz)
        logger.info(
            f"Created new_quiz version: {new_quiz.version} new_quiz {new_quiz.id} old_quiz {curr_quiz.id} by {acting_user_id}")

        return new_quiz

    async def publish_quiz(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID) -> QuizModel:
        await self._assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        options = [selectinload(QuizModel.questions).selectinload(QuestionModel.options)]
        quiz = await self.get_quiz(company_id=company_id, quiz_id=quiz_id, options=options)

        if len(quiz.questions) < 2:
            raise ResourceConflictException("Quiz must have at least 2 questions.")

        for q in quiz.questions:
            q_options: Sequence[AnswerOptionModel] = q.options

            text = (q.text[:50] + "..") if len(q.text) > 50 else q.text
            if len(q_options) < 2:
                raise ResourceConflictException(f"Question '{text}' is incomplete (needs 2+ options).")

            if not any(opt.is_correct for opt in q_options):
                raise ResourceConflictException(f"Question '{text}' has no correct answer marked.")

            if not any(not opt.is_correct for opt in q_options):
                raise ResourceConflictException(f"Question '{text}' has no incorrect answer marked.")

        if quiz.root_quiz_id:
            await self.repo.hide_other_versions(company_id=company_id, root_id=quiz.root_quiz_id,
                                                exclude_quiz_id=quiz.id, )

        quiz.is_published = True
        quiz.is_visible = True

        await self.repo.save_and_refresh(quiz)
        logger.info(f"Published quiz: {quiz.id} version {quiz.version} by {acting_user_id}")

        return quiz

    async def update_quiz(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID,
                          quiz_info: QuizUpdateRequestSchema, ) -> QuizModel:
        await self._assert_admin_permissions(company_id=company_id, user_id=acting_user_id)

        quiz = await self.get_quiz(company_id=company_id, quiz_id=quiz_id)
        quiz = self._update_instance(instance=quiz, new_data=quiz_info, by=acting_user_id)

        await self.repo.save_and_refresh(quiz)
        logger.info(f"Updated {self.display_name}: {quiz.id} by {acting_user_id}")

        return quiz

    async def update_question(self, company_id: UUID, acting_user_id: UUID, quiz_id: UUID, question_id: UUID,
                              question_info: QuestionUpdateRequestSchema, ) -> QuestionModel:
        await self._assert_admin_permissions(company_id=company_id, user_id=acting_user_id)
        await self._assert_quiz_not_published(company_id=company_id, quiz_id=quiz_id)

        question = await self.get_question(company_id=company_id, quiz_id=quiz_id, question_id=question_id)
        question = self._update_instance(instance=question, new_data=question_info, by=acting_user_id)

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
        question = await self.repo.get_question_or_none(company_id=company_id, quiz_id=quiz_id, question_id=question_id)
        self._assert_valid_question(question=question)
        return question

    @staticmethod
    def _assert_valid_question(question: QuestionModel | None) -> None:
        if not question:
            raise InstanceNotFoundException(instance_name="Question")

    async def _assert_admin_permissions(self, company_id: UUID, user_id: UUID) -> None:
        await self.company_member_service.assert_user_permissions(company_id=company_id, user_id=user_id,
                                                                  required_role=CompanyRole.ADMIN)

    async def _assert_owner_permissions(self, company_id: UUID, user_id: UUID) -> None:
        await self.company_member_service.assert_user_permissions(company_id=company_id, user_id=user_id,
                                                                  required_role=CompanyRole.OWNER)

    async def has_admin_permission(self, company_id: UUID, user_id: UUID) -> bool:
        """
        :param company_id:
        :param user_id:
        :return: True if admin, False otherwise.
        """
        return await self.company_member_service.has_user_permissions(company_id=company_id, user_id=user_id,
                                                                      required_role=CompanyRole.ADMIN)
