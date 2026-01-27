from typing import Any
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from src.core.exceptions import ResourceConflictException
from ..enums import AttemptStatus
from ..models import AttemptAnswerSelection as AttemptAnswerSelectionModel
from ..models import CompanyQuizQuestion as CompanyQuizQuestionModel
from ..models import QuestionAnswerOption as QuestionAnswerOptionModel
from ..models import QuizAttempt as QuizAttemptModel
from ..models import QuizAttemptAnswer as QuizAttemptAnswerModel


def assert_attempt_in_progress(status: AttemptStatus, is_expired: bool) -> None:
    if status != AttemptStatus.IN_PROGRESS:
        raise ResourceConflictException(
            message=f"Cannot save answer. Attempt is {status.value}"
        )
    if is_expired:
        raise ResourceConflictException("Attempt has expired.")


def get_finalize_attempt_options() -> list[ExecutableOption]:
    return [
        selectinload(QuizAttemptModel.quiz),
        selectinload(QuizAttemptModel.user),
        selectinload(QuizAttemptModel.answers).selectinload(
            QuizAttemptAnswerModel.selected_options
        ),
        selectinload(QuizAttemptModel.answers)
        .selectinload(QuizAttemptAnswerModel.question)
        .selectinload(CompanyQuizQuestionModel.options),
    ]


def get_attempt_details_options() -> list[ExecutableOption]:
    return [selectinload(QuizAttemptModel.answers), selectinload(QuizAttemptModel.quiz)]


def get_attempt_filters(
    user_id: UUID, attempt_id: UUID
) -> dict[InstrumentedAttribute, Any]:
    return {QuizAttemptModel.user_id: user_id, QuizAttemptModel.id: attempt_id}


def get_active_attempt_filters(
    user_id: UUID, quiz_id: UUID
) -> dict[InstrumentedAttribute, Any]:
    active_attempt_filters = {
        QuizAttemptModel.user_id: user_id,
        QuizAttemptModel.quiz_id: quiz_id,
        QuizAttemptModel.status: AttemptStatus.IN_PROGRESS,
    }
    return active_attempt_filters


def get_answer_filters(
    question_id: UUID, attempt_id: UUID
) -> dict[InstrumentedAttribute, Any]:
    return {
        QuizAttemptAnswerModel.attempt_id: attempt_id,
        QuizAttemptAnswerModel.question_id: question_id,
    }


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


def calc_score(correct_answers_count: int, total_questions_count: int) -> float:
    score = (
        (correct_answers_count / total_questions_count * 100.0)
        if total_questions_count > 0
        else 0.0
    )
    return score
