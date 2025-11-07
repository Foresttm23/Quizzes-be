import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, SecretStr


# Internal use
class User(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    hashed_password: SecretStr
    auth_provider: str
    is_banned: bool
    created_at: datetime

    model_config = {"from_attributes": True}
