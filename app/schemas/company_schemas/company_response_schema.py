from datetime import datetime
from uuid import UUID

from app.schemas.base_schemas import BaseResponseModel


class CompanyDetailsResponse(BaseResponseModel):
    id: UUID
    name: str
    description: str | None
    is_visible: bool
    created_at: datetime
    updated_at: datetime
