from datetime import datetime
from typing import Sequence

from pydantic import BaseModel, model_validator


class Base(BaseModel):
    model_config = {"from_attributes": True}


class BaseUpdateMixin(BaseModel):
    @model_validator(mode="after")
    def at_least_one_field_provided(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least 1 field to update.")
        return self


# Generic response, so we can reuse it for pagination routes
class PaginationResponse[T](Base):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    data: Sequence[T]


class ScoreStatsBase(Base):
    score: float
    total_correct_answers: int
    total_questions_answered: int


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime


class AttemptMixin(BaseModel):
    started_at: datetime
    finished_at: datetime | None
