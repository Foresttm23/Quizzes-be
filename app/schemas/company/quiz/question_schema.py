from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base_schemas import Base, BaseUpdateMixin
from app.schemas.company.quiz.answer_option_schema import AnswerOptionsCreateRequestSchema
from schemas.company.quiz.answer_option_schema import AnswerOptionsStudentResponseSchema


class QuestionOptionsMixin:
    @field_validator('options')
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
