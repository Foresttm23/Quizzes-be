from pydantic import EmailStr, Field, SecretStr

from app.schemas.base_schemas import Base


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
