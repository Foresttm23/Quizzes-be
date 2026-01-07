import uuid
from datetime import datetime

from pydantic import EmailStr, Field, SecretStr

from core.schemas import Base
from .enums import AuthProviderEnum, JWTTypeEnum


class JWTSchema(Base):
    sub: str
    email: EmailStr
    auth_provider: AuthProviderEnum


class JWTRefreshSchema(JWTSchema):
    sub: str
    type: JWTTypeEnum

class UserDetailsResponse(Base):
    id: uuid.UUID
    email: EmailStr
    username: str
    auth_provider: str
    is_banned: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(Base):
    access_token: str
    refresh_token: str
    token_type: str


class RegisterRequest(Base):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: SecretStr = Field(min_length=8)


class LoginRequest(Base):
    email: EmailStr
    password: SecretStr


# Assuming we will have more fields later
class UserInfoUpdateRequest(Base):
    username: str = Field(min_length=3, max_length=100)


class UserPasswordUpdateRequest(Base):
    current_password: SecretStr = Field(min_length=8)
    new_password: SecretStr = Field(min_length=8)
