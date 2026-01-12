from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.core.schemas import AttemptMixin, Base, BaseUpdateMixin, TimestampMixin
from src.quiz.enums import AttemptStatus


class QuestionAnswerOptionBaseSchema(Base):
    id: UUID
    question_id: UUID
    text: str


class QuestionAnswerOptionAdminSchema(QuestionAnswerOptionBaseSchema):
    is_correct: bool


class CompanyQuizQuestionBaseSchema(Base, TimestampMixin):
    id: UUID
    quiz_id: UUID
    text: str
    points: float


class CompanyQuizQuestionSchema(CompanyQuizQuestionBaseSchema):
    options: list[QuestionAnswerOptionBaseSchema]


class CompanyQuizQuestionAdminSchema(CompanyQuizQuestionBaseSchema):
    options: list[QuestionAnswerOptionAdminSchema]


class CompanyQuizBaseSchema(Base, TimestampMixin):
    id: UUID
    company_id: UUID
    title: str
    description: str

    allowed_attempts: int | None
    time_limit_minutes: int | None
    is_published: bool
    is_visible: bool

    root_quiz_id: UUID | None
    version: int


class CompanyQuizSchema(CompanyQuizBaseSchema):
    questions: list[CompanyQuizQuestionSchema]


class CompanyQuizAdminSchema(CompanyQuizBaseSchema):
    questions: list[CompanyQuizQuestionAdminSchema]


class AttemptAnswerSelectionBaseSchema(Base):
    id: UUID
    answer_id: UUID
    option_id: UUID


class AttemptAnswerSelectionSchema(AttemptAnswerSelectionBaseSchema):
    option: QuestionAnswerOptionBaseSchema


class AttemptAnswerSelectionAdminSchema(AttemptAnswerSelectionBaseSchema):
    option: QuestionAnswerOptionAdminSchema


class QuizAttemptAnswerBaseSchema(Base):
    id: UUID
    attempt_id: UUID
    question_id: UUID


class QuizAttemptAnswerSchema(QuizAttemptAnswerBaseSchema):
    selected_options: list[AttemptAnswerSelectionSchema]


class QuizAttemptAnswerAdminSchema(QuizAttemptAnswerBaseSchema):
    selected_options: list[AttemptAnswerSelectionAdminSchema]


class QuizAttemptBaseSchema(Base, AttemptMixin):
    id: UUID
    user_id: UUID
    quiz_id: UUID

    score: float
    correct_answers_count: int
    total_questions_count: int
    status: AttemptStatus
    expires_at: datetime | None = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) >= self.expires_at


class QuizAttemptSchema(QuizAttemptBaseSchema):
    answers: list[QuizAttemptAnswerSchema]


class QuizAttemptAdminSchema(QuizAttemptBaseSchema):
    answers: list[QuizAttemptAnswerAdminSchema]


# ----------------------------------------------- RELATION SPECIFIC -------------------------------------------------


class QuizAttemptAndQuizRelSchema(QuizAttemptSchema):
    quiz: CompanyQuizBaseSchema


class QuizAttemptAdminAndQuizRelSchema(QuizAttemptAdminSchema):
    quiz: CompanyQuizBaseSchema


# ----------------------------------------------- RESPONSES -------------------------------------------------


class QuizStartAttemptResponseSchema(Base):
    questions: list[CompanyQuizQuestionSchema]
    attempt: QuizAttemptSchema


class QuizReviewAttemptResponseSchema(Base):
    """End of attempt will return selected and correct options along the list of questions."""

    questions: list[CompanyQuizQuestionAdminSchema]
    attempt: QuizAttemptAdminSchema


# ----------------------------------------------- MIXIN -------------------------------------------------


class QuestionOptionsMixin(BaseModel):
    @field_validator("options")
    @classmethod
    def validate_option(cls, options: list[AnswerOptionsCreateRequestSchema] | None):
        if options is None:
            return options

        cls.validate_correct_option_exist(options=options)
        cls.validate_incorrect_option_exist(options=options)

        return options

    @classmethod
    def validate_correct_option_exist(
            cls, options: list[AnswerOptionsCreateRequestSchema]
    ):
        has_correct_answer = any(opt.is_correct for opt in options)

        if not has_correct_answer:
            raise ValueError("At least one option must be marked as correct.")

    @classmethod
    def validate_incorrect_option_exist(
            cls, options: list[AnswerOptionsCreateRequestSchema]
    ):
        has_incorrect_answer = any(not opt.is_correct for opt in options)

        if not has_incorrect_answer:
            raise ValueError("At least one option must be marked as incorrect.")


# ----------------------------------------------- REQUESTS -------------------------------------------------


class QuizCreateRequestSchema(Base):
    title: str = Field(max_length=128)
    description: str | None = Field(None, max_length=1024)
    time_limit_minutes: int | None = Field(
        None,
        ge=1,
        description="None=infinite, should be passed directly as None to take effect.",
    )


class QuizUpdateRequestSchema(Base, BaseUpdateMixin):
    title: str | None = Field(None, max_length=128)
    description: str | None = Field(None, max_length=1024)
    time_limit_minutes: int | None = Field(
        None,
        ge=1,
        description="None=infinite, should be passed directly as None to take effect.",
    )


class QuestionUpdateRequestSchema(Base, QuestionOptionsMixin, BaseUpdateMixin):
    text: str | None = Field(None, min_length=8, max_length=512)
    options: list[AnswerOptionsCreateRequestSchema] | None = Field(
        None, min_length=2, max_length=8
    )


class QuestionCreateRequestSchema(Base, QuestionOptionsMixin):
    text: str = Field(min_length=8, max_length=512)
    options: list[AnswerOptionsCreateRequestSchema] = Field(min_length=2, max_length=8)


class AnswerOptionsCreateRequestSchema(Base):
    text: str = Field(min_length=1, max_length=256)
    is_correct: bool = Field(False)


class SaveAnswerRequestSchema(Base):
    ids: list[UUID]
