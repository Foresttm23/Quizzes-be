import uuid
from datetime import datetime
from typing import Generic, TypeVar, List

from pydantic import BaseModel, EmailStr


class BaseResponseModel(BaseModel):
    model_config = {"from_attributes": True}


class UserDetailsResponse(BaseResponseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    auth_provider: str
    is_banned: bool
    created_at: datetime


T = TypeVar("T")


# Generic response, so we can reuse it for pagination routes
class PaginationResponse(BaseResponseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    data: List[T]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
