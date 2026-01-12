from typing import Any, Sequence
from typing import TypeVar
from uuid import UUID, uuid4

from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.sql.base import ExecutableOption

from src.core.exceptions import InstanceNotFoundException, ResourceConflictException
from .enums import AttemptStatus
from .models import AttemptAnswerSelection as AttemptAnswerSelectionModel
from .models import CompanyQuiz as CompanyQuizModel
from .models import CompanyQuizQuestion as CompanyQuizQuestionModel
from .models import QuestionAnswerOption as QuestionAnswerOptionModel
from .models import QuizAttempt as QuizAttemptModel
from .models import QuizAttemptAnswer as QuizAttemptAnswerModel
from .schemas import (QuestionUpdateRequestSchema, )

Q = TypeVar("Q")


class QuizUtils:
    def __init__(self):
        pass

    @staticmethod
    def calc_correct_answers_count(attempt: QuizAttemptModel) -> int:
        """
        Calculate the score strictly. Must ensure attempt fields are loaded.
        :param attempt: attempt.answers, answer.selected_options, question.options
        :return: correct_answer_count: int, score: float
        """
        correct_answers_count = 0
        for answer in attempt.answers:
            question: CompanyQuizQuestionModel = answer.question
            user_selections: list[AttemptAnswerSelectionModel] = answer.selected_options
            q_options: list[QuestionAnswerOptionModel] = question.options

            selected_ids = {sel.option_id for sel in user_selections}
            correct_ids = {opt.id for opt in q_options if opt.is_correct}

            if selected_ids == correct_ids:
                correct_answers_count += 1

        return correct_answers_count

    @staticmethod
    def calc_score(correct_answers_count: int, total_questions_count: int) -> float:
        score = ((correct_answers_count / total_questions_count * 100.0) if total_questions_count > 0 else 0.0)
        return score

    @staticmethod
    def validate_quiz(quiz: CompanyQuizModel) -> None:
        """
        Validates quiz fields before publishing(Ensure questions>2 and at least 1 correct and 1 incorrect.). Must ensure quiz fields are loaded.
        :param quiz: Ensure loaded quiz.questions, question.options
        :return:
        """
        if len(quiz.questions) < 2:
            raise ResourceConflictException("Quiz must have at least 2 questions.")

        for q in quiz.questions:
            q_options: Sequence[QuestionAnswerOptionModel] = q.options

            text = (q.text[:50] + "..") if len(q.text) > 50 else q.text
            if len(q_options) < 2:
                raise ResourceConflictException(f"Question '{text}' is incomplete (needs 2+ options).")

            if not any(opt.is_correct for opt in q_options):
                raise ResourceConflictException(f"Question '{text}' has no correct answer marked.")

            if not any(not opt.is_correct for opt in q_options):
                raise ResourceConflictException(f"Question '{text}' has no incorrect answer marked.")

    @staticmethod
    def get_visible_quiz_filters(company_id: UUID, quiz_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {CompanyQuizModel.company_id: company_id, CompanyQuizModel.id: quiz_id,
                   CompanyQuizModel.is_published: True, CompanyQuizModel.is_visible: True, }
        return filters

    @staticmethod
    def get_all_quiz_filters(company_id: UUID, quiz_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {CompanyQuizModel.company_id: company_id, CompanyQuizModel.id: quiz_id, }
        return filters

    @staticmethod
    def assert_valid_question(question: Q | None, ) -> Q:
        if not question:
            raise InstanceNotFoundException(instance_name="Question")
        return question

    @staticmethod
    def get_visible_quizzes_filters(company_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {CompanyQuizModel.company_id: company_id, CompanyQuizModel.is_visible: True,
                   CompanyQuizModel.is_published: True, }
        return filters

    @staticmethod
    def get_all_quizzes_filters(company_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {CompanyQuizModel.company_id: company_id}
        return filters

    @staticmethod
    def update_question_options(question: CompanyQuizQuestionModel,
                                full_question_info: QuestionUpdateRequestSchema, ) -> CompanyQuizQuestionModel:
        if full_question_info.options is None:
            return question

        question.options.clear()
        for opt in full_question_info.options:
            new_opt = QuestionAnswerOptionModel(id=uuid4(), text=opt.text, is_correct=opt.is_correct,
                                                question_id=question.id, )
            question.options.append(new_opt)

        return question


class AttemptUtils:
    def __init__(self):
        pass

    @staticmethod
    def assert_attempt_in_progress(status: AttemptStatus, is_expired: bool) -> None:
        if status != AttemptStatus.IN_PROGRESS:
            raise ResourceConflictException(message=f"Cannot save answer. Attempt is {status.value}")
        if is_expired:
            raise ResourceConflictException("Attempt has expired.")

    @staticmethod
    def get_finalize_attempt_options() -> list[ExecutableOption]:
        return [selectinload(QuizAttemptModel.quiz), selectinload(QuizAttemptModel.user),
                selectinload(QuizAttemptModel.answers).selectinload(QuizAttemptAnswerModel.selected_options),
                selectinload(QuizAttemptModel.answers).selectinload(QuizAttemptAnswerModel.question).selectinload(
                    CompanyQuizQuestionModel.options)]

    @staticmethod
    def get_attempt_details_options() -> list[ExecutableOption]:
        return [selectinload(QuizAttemptModel.answers), selectinload(QuizAttemptModel.quiz)]

    @staticmethod
    def get_attempt_filters(user_id: UUID, attempt_id: UUID) -> dict[InstrumentedAttribute, Any]:
        return {QuizAttemptModel.user_id: user_id, QuizAttemptModel.id: attempt_id}

    @staticmethod
    def get_active_attempt_filters(user_id: UUID, quiz_id: UUID) -> dict[InstrumentedAttribute, Any]:
        active_attempt_filters = {QuizAttemptModel.user_id: user_id, QuizAttemptModel.quiz_id: quiz_id,
                                  QuizAttemptModel.status: AttemptStatus.IN_PROGRESS}
        return active_attempt_filters

    @staticmethod
    def get_answer_filters(question_id: UUID, attempt_id: UUID) -> dict[InstrumentedAttribute, Any]:
        return {QuizAttemptAnswerModel.attempt_id: attempt_id, QuizAttemptAnswerModel.question_id: question_id}
