from datetime import datetime
from uuid import UUID

from app.schemas.base_schemas import BaseResponseModel
from app.schemas.user_schemas.user_response_schema import UserDetailsResponse
from app.utils.enum_utils import CompanyRole


class CompanyMemberDetailsResponse(BaseResponseModel):
    company_id: UUID
    user_id: UUID
    role: CompanyRole
    joined_at: datetime
    user: UserDetailsResponse
