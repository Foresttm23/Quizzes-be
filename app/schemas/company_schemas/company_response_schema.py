from typing import List
from uuid import UUID

from app.schemas.base_schemas import BaseResponseModel


class CompanyDetailsResponse(BaseResponseModel):
    id: UUID
    name: str
    description: str | None
    owner_id: UUID
    admins: list[UUID] = []
    is_visible: bool
    created_at: str
    updated_at: str


class CompanyListResponse(BaseResponseModel):
    total: int
    page: int
    page_size: int
    items: List[CompanyDetailsResponse]
