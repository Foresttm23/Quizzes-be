from datetime import datetime
from uuid import UUID

from app.schemas.base_schemas import BaseResponseModel
from app.schemas.company_members_schemas.company_member_response_schema import CompanyMemberDetailsResponse
from app.utils.enum_utils import MessageStatus
from schemas.base_schemas import BaseRequestModel


class UpdateRequestSchema(BaseResponseModel):
    status: MessageStatus


class UpdateInvitationSchema(BaseResponseModel):
    invitation_status: MessageStatus


class RequestDetailsResponse(BaseResponseModel):
    id: UUID
    company_id: UUID
    requesting_user_id: UUID
    status: MessageStatus
    created_at: datetime
    updated_at: datetime


class AcceptRequestResponse(BaseResponseModel):
    request: RequestDetailsResponse
    new_member: CompanyMemberDetailsResponse


class InvitationDetailsResponse(BaseResponseModel):
    id: UUID
    company_id: UUID
    invited_user_id: UUID
    status: MessageStatus
    created_at: datetime
    updated_at: datetime


class AcceptInvitationResponse(BaseResponseModel):
    invitation: InvitationDetailsResponse
    new_member: CompanyMemberDetailsResponse


class CreateInvitationRequest(BaseRequestModel):
    invited_user_id: UUID
