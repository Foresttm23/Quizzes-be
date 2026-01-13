from typing import Any, Sequence, TypeVar
from uuid import UUID, uuid4

from sqlalchemy.orm import InstrumentedAttribute

from src.core.exceptions import InstanceNotFoundException, ResourceConflictException
from ..models import CompanyQuiz as CompanyQuizModel
from ..models import CompanyQuizQuestion as CompanyQuizQuestionModel
from ..models import QuestionAnswerOption as QuestionAnswerOptionModel
from ..schemas import (QuestionUpdateRequestSchema, )

Q = TypeVar("Q")


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


def get_visible_quiz_filters(company_id: UUID, quiz_id: UUID) -> dict[InstrumentedAttribute, Any]:
    filters = {CompanyQuizModel.company_id: company_id, CompanyQuizModel.id: quiz_id,
               CompanyQuizModel.is_published: True, CompanyQuizModel.is_visible: True, }
    return filters


def get_all_quiz_filters(company_id: UUID, quiz_id: UUID) -> dict[InstrumentedAttribute, Any]:
    filters = {CompanyQuizModel.company_id: company_id, CompanyQuizModel.id: quiz_id, }
    return filters


def assert_valid_question(question: Q | None, ) -> Q:
    if not question:
        raise InstanceNotFoundException(instance_name="Question")
    return question


def get_visible_quizzes_filters(company_id: UUID) -> dict[InstrumentedAttribute, Any]:
    filters = {CompanyQuizModel.company_id: company_id, CompanyQuizModel.is_visible: True,
               CompanyQuizModel.is_published: True, }
    return filters


def get_all_quizzes_filters(company_id: UUID) -> dict[InstrumentedAttribute, Any]:
    filters = {CompanyQuizModel.company_id: company_id}
    return filters


def update_question_options(question: CompanyQuizQuestionModel,
                            full_question_info: QuestionUpdateRequestSchema, ) -> CompanyQuizQuestionModel:
    """Options must be loaded."""
    if full_question_info.options is None:
        return question

    question.options.clear()
    for opt in full_question_info.options:
        new_opt = QuestionAnswerOptionModel(id=uuid4(), text=opt.text, is_correct=opt.is_correct,
                                            question_id=question.id, )
        question.options.append(new_opt)

    return question
