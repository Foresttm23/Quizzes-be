from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base_schemas import Base
from app.schemas.base_schemas import BaseUpdateMixin


class CompanyCreateRequestSchema(Base, BaseUpdateMixin):
    name: str
    description: str | None = Field(None, max_length=255)
    is_visible: bool | None


class CompanyUpdateInfoRequestSchema(Base, BaseUpdateMixin):
    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=255)
    is_visible: bool | None


class CompanyDetailsResponseSchema(Base):
    id: UUID
    name: str
    description: str | None
    is_visible: bool
    created_at: datetime
    updated_at: datetime
