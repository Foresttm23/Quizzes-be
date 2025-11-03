from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, SecretStr


# Internal use
class User(BaseModel):
    id: int
    email: EmailStr
    username: str
    hashed_password: SecretStr
    created_at: datetime

    class Config:
        from_attributes = True


class SignUpRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: SecretStr = Field(min_length=8)


class SignInRequest(BaseModel):
    email: Optional[EmailStr]
    password: SecretStr


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[SecretStr] = Field(None, min_length=8)


class UserDetailsResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    created_at: datetime


class UsersListResponse(BaseModel):
    users: List[UserDetailsResponse]
