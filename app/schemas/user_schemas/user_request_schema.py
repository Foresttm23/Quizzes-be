from typing import Optional

from pydantic import BaseModel, EmailStr, Field, SecretStr


class SignUpRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: SecretStr = Field(min_length=8)


class SignInRequest(BaseModel):
    email: Optional[EmailStr]
    password: SecretStr


# Assuming we will have more fields later
class UserInfoUpdateRequest(BaseModel):
    username: str = Field(None, min_length=3, max_length=100)


class UserPasswordUpdateRequest(BaseModel):
    current_password: SecretStr
    new_password: SecretStr = Field(min_length=8)
