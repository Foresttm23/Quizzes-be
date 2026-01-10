from typing import Any, Sequence, TypeVar
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from src.core.exceptions import InstanceNotFoundException, ResourceConflictException

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
        score = (correct_answers_count / total_questions_count * 100.0) if total_questions_count > 0 else 0.0
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
        filters = {
            CompanyQuizModel.company_id: company_id,
            CompanyQuizModel.id: quiz_id,
            CompanyQuizModel.is_published: True,
            CompanyQuizModel.is_visible: True,
        }
        return filters

    @staticmethod
    def get_all_quiz_filters(company_id: UUID, quiz_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {CompanyQuizModel.company_id: company_id, CompanyQuizModel.id: quiz_id}
        return filters

    @staticmethod
    def assert_valid_question(
        question: Q | None,
    ) -> Q:
        if not question:
            raise InstanceNotFoundException(instance_name="Question")
        return question
