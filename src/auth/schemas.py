import uuid
from datetime import datetime

from pydantic import EmailStr, Field, SecretStr

from src.core.schemas import Base, ScoreStatsBase, TimestampMixin

from .enums import AuthProviderEnum, JWTTypeEnum


class JWTSchema(Base):
    sub: str
    email: EmailStr
    auth_provider: AuthProviderEnum


class JWTRefreshSchema(JWTSchema):
    sub: str
    type: JWTTypeEnum


# ----------------------------------------------- RESPONSES -------------------------------------------------


class UserDetailsResponse(Base, TimestampMixin):
    id: uuid.UUID
    email: EmailStr
    username: str
    auth_provider: str
    is_banned: bool
    last_quiz_attempt_at: datetime | None


class TokenResponse(Base):
    access_token: str
    refresh_token: str
    token_type: str


class UserAverageSystemStatsResponseSchema(ScoreStatsBase):
    pass


# ----------------------------------------------- REQUESTS -------------------------------------------------


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
