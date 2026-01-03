from uuid import UUID

from pydantic import Field

from app.schemas.base_schemas import Base


class AnswerOptionsCreateRequestSchema(Base):
    text: str = Field(min_length=1, max_length=256)
    is_correct: bool = Field(False)


class AnswerOptionsStudentResponseSchema(Base):
    id: UUID
    question_id: UUID
    text: str


class AnswerOptionsAdminResponseSchema(Base, AnswerOptionsStudentResponseSchema):
    is_correct: bool
