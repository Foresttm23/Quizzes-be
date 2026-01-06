from datetime import datetime
from uuid import UUID

from app.schemas.base_schemas import Base
from app.schemas.user.user_response_schema import UserDetailsResponse
from app.utils.enum_utils import CompanyRole


class CompanyMemberDetailsResponse(Base):
    company_id: UUID
    user_id: UUID
    role: CompanyRole
    joined_at: datetime
    user: UserDetailsResponse


class UpdateMemberRoleSchema(Base):
    role: CompanyRole
