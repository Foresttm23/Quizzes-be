from datetime import datetime
from uuid import UUID

from app.schemas.base_schemas import Base
from app.utils.enum_utils import MessageStatus
from schemas.company.member_schema import CompanyMemberDetailsResponse


class UpdateRequestSchema(Base):
    status: MessageStatus


class UpdateInvitationSchema(Base):
    invitation_status: MessageStatus


class RequestDetailsResponse(Base):
    id: UUID
    company_id: UUID
    requesting_user_id: UUID
    status: MessageStatus
    created_at: datetime
    updated_at: datetime


class AcceptRequestResponse(Base):
    request: RequestDetailsResponse
    new_member: CompanyMemberDetailsResponse


class InvitationDetailsResponse(Base):
    id: UUID
    company_id: UUID
    invited_user_id: UUID
    status: MessageStatus
    created_at: datetime
    updated_at: datetime


class AcceptInvitationResponse(Base):
    invitation: InvitationDetailsResponse
    new_member: CompanyMemberDetailsResponse


class CreateInvitationRequest(Base):
    invited_user_id: UUID
