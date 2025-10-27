from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    email: EmailStr
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class SignUpRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class SignInRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None


class UsersListResponse(BaseModel):
    users: List[User]


class UserDetailsResponse(BaseModel):
    user: User
