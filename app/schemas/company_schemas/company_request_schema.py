from pydantic import Field

from app.schemas.base_schemas import BaseRequestModel


class CompanyCreateRequest(BaseRequestModel):
    name: str
    description: str | None = Field(None, max_length=255)


class CompanyUpdateInfoRequest(BaseRequestModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=255)
    is_visible: bool | None
