from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from core.schemas import Base, BaseUpdateMixin


class QuizCreateRequestSchema(Base):
    title: str = Field(max_length=128)
    description: str | None = Field(None, max_length=1024)


class QuizUpdateRequestSchema(Base, BaseUpdateMixin):
    title: str | None = Field(None, max_length=128)
    description: str | None = Field(None, max_length=1024)


class QuizDetailsResponseSchema(Base):
    id: UUID
    company_id: UUID

    title: str
    description: str

    allowed_attempts: int | None

    is_published: bool
    is_visible: bool

    root_quiz_id: UUID | None
    version: int

    updated_at: datetime
    created_at: datetime

    total_attempts: int
    questions_count: int


class QuestionOptionsMixin:
    @field_validator("options")
    @classmethod
    def validate_option(cls, options: list[AnswerOptionsCreateRequestSchema] | None):
        if options is None:
            return options

        cls.validate_correct_option_exist(options=options)
        cls.validate_incorrect_option_exist(options=options)

        return options

    @classmethod
    def validate_correct_option_exist(cls, options: list[AnswerOptionsCreateRequestSchema]):
        has_correct_answer = any(opt.is_correct for opt in options)

        if not has_correct_answer:
            raise ValueError("At least one option must be marked as correct.")

    @classmethod
    def validate_incorrect_option_exist(cls, options: list[AnswerOptionsCreateRequestSchema]):
        has_incorrect_answer = any(not opt.is_correct for opt in options)

        if not has_incorrect_answer:
            raise ValueError("At least one option must be marked as incorrect.")


class QuestionUpdateRequestSchema(Base, QuestionOptionsMixin, BaseUpdateMixin):
    text: str | None = Field(None, min_length=8, max_length=512)
    options: list[AnswerOptionsCreateRequestSchema] | None = Field(None, min_length=2, max_length=8)


class QuestionCreateRequestSchema(Base, QuestionOptionsMixin):
    text: str = Field(min_length=8, max_length=512)
    options: list[AnswerOptionsCreateRequestSchema] = Field(min_length=2, max_length=8)


class QuestionUserResponseSchema(Base):
    id: UUID
    quiz_id: UUID

    text: str
    options: list[AnswerOptionsStudentResponseSchema]


class QuestionAdminResponseSchema(Base, QuestionUserResponseSchema):
    options: list[AnswerOptionsStudentResponseSchema]


class AnswerOptionsCreateRequestSchema(Base):
    text: str = Field(min_length=1, max_length=256)
    is_correct: bool = Field(False)


class AnswerOptionsStudentResponseSchema(Base):
    id: UUID
    question_id: UUID
    text: str


class AnswerOptionsAdminResponseSchema(Base, AnswerOptionsStudentResponseSchema):
    is_correct: bool


class SaveAnswerRequestSchema(Base):
    ids: list[UUID]
