from typing import Generic, TypeVar, Any, Sequence

from pydantic import BaseModel, model_validator

from app.core.exceptions import FieldsNotProvidedException


class BaseResponseModel(BaseModel):
    model_config = {"from_attributes": True}


class BaseRequestModel(BaseModel):
    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    def at_least_one_field_provided(cls, values: dict[str, Any]):
        if not any(v is not None for v in values.values()):
            raise FieldsNotProvidedException()
        return values


T = TypeVar("T")


# Generic response, so we can reuse it for pagination routes
class PaginationResponse(BaseResponseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    data: Sequence[T]
