from typing import Any
from uuid import UUID

from sqlalchemy import case
from sqlalchemy.orm import InstrumentedAttribute, selectinload
from sqlalchemy.sql.base import ExecutableOption

from src.core.exceptions import ResourceConflictException

from ..enums import AttemptStatus
from ..models import AttemptAnswerSelection as AttemptAnswerSelectionModel
from ..models import CompanyQuizQuestion as CompanyQuizQuestionModel
from ..models import QuestionAnswerOption as QuestionAnswerOptionModel
from ..models import QuizAttempt as QuizAttemptModel
from ..models import QuizAttemptAnswer as QuizAttemptAnswerModel


def assert_in_progress(
    attempt: QuizAttemptModel,
) -> None:  # TODO pass the task to the worker to invalidate the quiz.
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise ResourceConflictException(
            message=f"Cannot save answer. Attempt is {attempt.status.value}"
        )
    if attempt.is_expired:
        raise ResourceConflictException("Attempt has expired.")


def finalize_attempt_options() -> list[ExecutableOption]:
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


def assert_viewable(attempt: Any, is_admin: bool) -> None:
    is_finished = attempt.status != AttemptStatus.IN_PROGRESS
    is_viewable = is_finished or attempt.is_expired or is_admin

    if not is_viewable:
        raise  # TODO raise error that indicate that provided attempt is still ongoing


def user_attempts_order_rules():
    status_priority = case(
        {
            AttemptStatus.IN_PROGRESS: 1,
            AttemptStatus.COMPLETED: 2,
            AttemptStatus.EXPIRED: 3,
        },
        value=QuizAttemptModel.status,
    )

    order_rules = [status_priority, QuizAttemptModel.started_at.desc()]
    return order_rules


def attempt_filters(
    user_id: UUID, attempt_id: UUID
) -> dict[InstrumentedAttribute, Any]:
    return {QuizAttemptModel.user_id: user_id, QuizAttemptModel.id: attempt_id}


def attempt_filters_by_quiz(
    user_id: UUID, quiz_id: UUID
) -> dict[InstrumentedAttribute, Any]:
    filters = {
        QuizAttemptModel.user_id: user_id,
        QuizAttemptModel.quiz_id: quiz_id,
    }
    return filters


def answer_filters(
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
