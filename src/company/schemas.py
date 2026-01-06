from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from auth.schemas import UserDetailsResponse
from core.schemas import Base, BaseUpdateMixin
from .enums import CompanyRole, MessageStatus


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


class CompanyMemberDetailsResponse(Base):
    company_id: UUID
    user_id: UUID
    role: CompanyRole
    joined_at: datetime
    user: UserDetailsResponse


class UpdateMemberRoleSchema(Base):
    role: CompanyRole
