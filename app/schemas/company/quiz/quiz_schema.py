from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base_schemas import Base
from schemas.base_schemas import BaseUpdateMixin


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
