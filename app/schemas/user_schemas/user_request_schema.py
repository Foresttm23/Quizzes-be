from pydantic import EmailStr, Field, SecretStr

from app.schemas.base_schemas import BaseRequestModel


class SignUpRequest(BaseRequestModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: SecretStr = Field(min_length=8)


class SignInRequest(BaseRequestModel):
    email: EmailStr | None = None
    password: SecretStr | None = None


# Assuming we will have more fields later
class UserInfoUpdateRequest(BaseRequestModel):
    username: str = Field(min_length=3, max_length=100)


class UserPasswordUpdateRequest(BaseRequestModel):
    current_password: SecretStr = Field(min_length=8)
    new_password: SecretStr = Field(min_length=8)
