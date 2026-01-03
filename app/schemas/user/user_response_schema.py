import uuid
from datetime import datetime

from pydantic import EmailStr

from app.schemas.base_schemas import Base


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
