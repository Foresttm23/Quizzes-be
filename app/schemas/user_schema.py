import uuid
from datetime import datetime
from typing import Generic, TypeVar, Optional, List

from pydantic import BaseModel, EmailStr, Field, SecretStr


# Internal use
class User(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    hashed_password: SecretStr
    created_at: datetime

    model_config = {"from_attributes": True}


class SignUpRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: SecretStr = Field(min_length=8)


class SignInRequest(BaseModel):
    email: Optional[EmailStr]
    password: SecretStr


class UserUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[SecretStr] = Field(None, min_length=8)


class BaseResponseModel(BaseModel):
    model_config = {"from_attributes": True}


class UserDetailsResponse(BaseResponseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
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
