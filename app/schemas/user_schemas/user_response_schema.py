import uuid
from datetime import datetime

from pydantic import EmailStr

from app.schemas.base_schemas import BaseResponseModel


class UserDetailsResponse(BaseResponseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    auth_provider: str
    is_banned: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseResponseModel):
    access_token: str
    refresh_token: str
    token_type: str
