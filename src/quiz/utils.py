from typing import Sequence, Any
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from src.core.exceptions import ResourceConflictException
from .models import AttemptAnswerSelection as AttemptAnswerSelectionModel, CompanyQuiz as QuizModel, \
    CompanyQuizQuestion as QuestionModel, QuizAttempt as AttemptModel, QuestionAnswerOption as AnswerOptionModel


class QuizUtils:
    def __init__(self):
        pass

    @staticmethod
    def calc_score(attempt: AttemptModel) -> float:
        """
        Calculate the score strictly. Must ensure attempt fields are loaded.
        :param attempt: attempt.answers, answer.selected_options, question.options
        :return:float
        """
        score = 0.0
        for answer in attempt.answers:
            question: QuestionModel = answer.question
            user_selections: list[AttemptAnswerSelectionModel] = answer.selected_options
            q_options: list[AnswerOptionModel] = question.options

            selected_ids = {opt.id for opt in user_selections}
            correct_ids = {opt.id for opt in q_options if opt.is_correct}

            if selected_ids == correct_ids:
                score += question.points

        return score

    @staticmethod
    def validate_quiz(quiz: QuizModel) -> None:
        """
        Validates quiz fields before publishing(Ensure questions>2 and at least 1 correct and 1 incorrect.). Must ensure quiz fields are loaded.
        :param quiz: Ensure loaded quiz.questions, question.options
        :return:
        """
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

    @classmethod
    def get_visible_quiz_filters(cls, company_id: UUID, quiz_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {QuizModel.company_id: company_id, QuizModel.id: quiz_id, QuizModel.is_published: True,
                   QuizModel.is_visible: True, }
        return filters

    @classmethod
    def get_all_quiz_filters(cls, company_id: UUID, quiz_id: UUID) -> dict[InstrumentedAttribute, Any]:
        filters = {QuizModel.company_id: company_id, QuizModel.id: quiz_id}
        return filters
