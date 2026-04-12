from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi_cache.decorator import cache

from auth.dependencies import GetOptionalUserJWTDep, GetUserJWTDep
from core.caching.keys import endpoint_key_builder
from core.dependencies import PaginationParamDep
from core.schemas import PaginationResponse
from quiz.dependencies import AttemptServiceDep
from .dependencies import (
    CompanyInvitationServiceDep,
    CompanyJoinRequestServiceDep,
    CompanyLimitDep,
    CompanyMemberServiceDep,
    CompanyServiceDep,
    InvLimitDep,
    ReqLimitDep,
)
from .enums import CompanyRole
from .schemas import (
    AcceptInvitationResponse,
    AcceptRequestResponse,
    CompanyCreateRequestSchema,
    CompanyDetailsResponseSchema,
    CompanyMemberDetailsResponse,
    CompanyUpdateInfoRequestSchema,
    CreateInvitationRequest,
    InvitationDetailsResponse,
    RequestDetailsResponse,
    UpdateMemberRoleSchema,
    UserAverageCompanyStatsResponseSchema,
)

companies_router = APIRouter(
    prefix="/companies", tags=["Companies"], dependencies=[CompanyLimitDep]
)
requests_router = APIRouter(
    prefix="/company-join-requests",
    tags=["Company Join Requests"],
    dependencies=[ReqLimitDep],
)
invitations_router = APIRouter(
    prefix="/company-invitations",
    tags=["Company Invitations"],
    dependencies=[InvLimitDep],
)


@companies_router.post(
    "/",
    response_model=CompanyDetailsResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_company(
    company_service: CompanyServiceDep,
    user: GetUserJWTDep,
    company_info: CompanyCreateRequestSchema,
):
    """
    Creates a company for authenticated user.
    This user is owner of the created company.
    """
    company = await company_service.create_company(
        acting_user_id=user.id, company_info=company_info
    )
    return company


@companies_router.get(
    "/",
    response_model=PaginationResponse[CompanyDetailsResponseSchema],
    status_code=status.HTTP_200_OK,
)
@cache(expire=600, key_builder=endpoint_key_builder)
async def get_companies(
    company_service: CompanyServiceDep,
    user: GetOptionalUserJWTDep,
    pagination: PaginationParamDep,
):
    """
    Get all companies by page and page_size.
    Filters can be added later.
    Crud operations in company_repository supports it.
    """
    user_id = user.id if user else None
    companies_data = await company_service.get_companies_paginated(
        page=pagination.page, page_size=pagination.page_size, user_id=user_id
    )
    return companies_data


@companies_router.get(
    "/{company_id}",
    response_model=CompanyDetailsResponseSchema,
    status_code=status.HTTP_200_OK,
)
@cache(expire=600, key_builder=endpoint_key_builder)
async def get_company(
    company_service: CompanyServiceDep, user: GetOptionalUserJWTDep, company_id: UUID
):
    """Returns a company by its id"""
    user_id = user.id if user else None
    company = await company_service.get_by_id(company_id=company_id, user_id=user_id)
    return company


@companies_router.patch(
    "/{company_id}",
    response_model=CompanyDetailsResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def update_company(
    company_service: CompanyServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
    new_company_info: CompanyUpdateInfoRequestSchema,
):
    """
    Updates a company by its id,
    if company.owner_id is equal to the currently authenticated user id.
    """
    updated_company = await company_service.update_company(
        company_id=company_id, acting_user_id=user.id, company_info=new_company_info
    )
    return updated_company


@companies_router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_service: CompanyServiceDep, user: GetUserJWTDep, company_id: UUID
):
    """
    Deletes a company by its id,
    if company.owner_id is equal to the currently authenticated user id.
    """
    await company_service.delete_company(company_id=company_id, acting_user_id=user.id)


# -------------


@companies_router.post(
    "/{company_id}/invitations",
    response_model=InvitationDetailsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    company_invitation_service: CompanyInvitationServiceDep,
    acting_user: GetUserJWTDep,
    company_id: UUID,
    request_data: CreateInvitationRequest,
):
    invitation = await company_invitation_service.create_invitation(
        company_id=company_id,
        invited_user_id=request_data.invited_user_id,
        acting_user_id=acting_user.id,
    )

    return invitation


@invitations_router.patch(
    "/{invitation_id}/accept",
    response_model=AcceptInvitationResponse,
    status_code=status.HTTP_200_OK,
)
async def accept_invitation(
    company_invitation_service: CompanyInvitationServiceDep,
    invited_user: GetUserJWTDep,
    invitation_id: UUID,
):
    invitation, new_member = await company_invitation_service.accept_from_company(
        invitation_id=invitation_id, invited_user_id=invited_user.id
    )
    return {"invitation": invitation, "new_member": new_member}


@invitations_router.patch(
    "/{invitation_id}/decline",
    response_model=InvitationDetailsResponse,
    status_code=status.HTTP_200_OK,
)
async def decline_invitation(
    company_invitation_service: CompanyInvitationServiceDep,
    invited_user: GetUserJWTDep,
    invitation_id: UUID,
):
    invitation = await company_invitation_service.decline_from_company(
        invitation_id=invitation_id, invited_user_id=invited_user.id
    )
    return invitation


@invitations_router.patch(
    "/{invitation_id}/cancel",
    response_model=InvitationDetailsResponse,
    status_code=status.HTTP_200_OK,
)
async def cancel_invitation(
    company_invitation_service: CompanyInvitationServiceDep,
    acting_user: GetUserJWTDep,
    invitation_id: UUID,
):
    invitation = await company_invitation_service.cancel_by_company(
        invitation_id=invitation_id, acting_user_id=acting_user.id
    )
    return invitation


@companies_router.get(
    "/{company_id}/invitations/pending",
    response_model=PaginationResponse[InvitationDetailsResponse],
    status_code=status.HTTP_200_OK,
)
@cache(expire=600, key_builder=endpoint_key_builder)
async def get_company_pending_invitations(
    company_invitation_service: CompanyInvitationServiceDep,
    acting_user: GetUserJWTDep,
    company_id: UUID,
    pagination: PaginationParamDep,
):
    requests = await company_invitation_service.get_pending_for_company(
        company_id=company_id,
        acting_user_id=acting_user.id,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return requests


@invitations_router.get(
    "/my-pending",
    response_model=PaginationResponse[InvitationDetailsResponse],
    status_code=status.HTTP_200_OK,
)
@cache(expire=600, key_builder=endpoint_key_builder)
async def get_my_pending_invitations(
    company_invitation_service: CompanyInvitationServiceDep,
    user: GetUserJWTDep,
    pagination: PaginationParamDep,
):
    requests = await company_invitation_service.get_pending_for_user(
        user_id=user.id, page=pagination.page, page_size=pagination.page_size
    )
    return requests


# -------------


@companies_router.post(
    "/{company_id}/join-requests",
    response_model=RequestDetailsResponse,
    status_code=status.HTTP_200_OK,
)
async def create_join_request(
    company_join_request_service: CompanyJoinRequestServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
):
    request = await company_join_request_service.create_join_request(
        company_id=company_id, requesting_user_id=user.id
    )
    return request


@requests_router.patch(
    "/{request_id}/accept",
    response_model=AcceptRequestResponse,
    status_code=status.HTTP_200_OK,
)
async def accept_request(
    company_join_request_service: CompanyJoinRequestServiceDep,
    acting_user: GetUserJWTDep,
    request_id: UUID,
):
    request, new_member = await company_join_request_service.accept_request(
        request_id=request_id, acting_user_id=acting_user.id
    )
    return {"request": request, "new_member": new_member}


@requests_router.patch(
    "/{request_id}/decline",
    response_model=RequestDetailsResponse,
    status_code=status.HTTP_200_OK,
)
async def decline_request(
    company_join_request_service: CompanyJoinRequestServiceDep,
    acting_user: GetUserJWTDep,
    request_id: UUID,
):
    request = await company_join_request_service.decline_request(
        request_id=request_id, acting_user_id=acting_user.id
    )
    return request


@requests_router.patch(
    "/{request_id}/cancel",
    response_model=RequestDetailsResponse,
    status_code=status.HTTP_200_OK,
)
async def cancel_request(
    company_join_request_service: CompanyJoinRequestServiceDep,
    requesting_user: GetUserJWTDep,
    request_id: UUID,
):
    request = await company_join_request_service.cancel_request(
        request_id=request_id, requesting_user_id=requesting_user.id
    )
    return request


@companies_router.get(
    "/{company_id}/join-requests/pending",
    response_model=PaginationResponse[RequestDetailsResponse],
    status_code=status.HTTP_200_OK,
)
@cache(expire=600, key_builder=endpoint_key_builder)
async def get_company_pending_requests(
    company_join_request_service: CompanyJoinRequestServiceDep,
    acting_user: GetUserJWTDep,
    company_id: UUID,
    pagination: PaginationParamDep,
):
    requests = await company_join_request_service.get_pending_for_company(
        company_id=company_id,
        acting_user_id=acting_user.id,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return requests


@requests_router.get(
    "/my-pending",
    response_model=PaginationResponse[RequestDetailsResponse],
    status_code=status.HTTP_200_OK,
)
@cache(expire=60, key_builder=endpoint_key_builder)
async def get_my_pending_requests(
    company_join_request_service: CompanyJoinRequestServiceDep,
    user: GetUserJWTDep,
    pagination: PaginationParamDep,
):
    requests = await company_join_request_service.get_pending_for_user(
        user_id=user.id, page=pagination.page, page_size=pagination.page_size
    )
    return requests


# ----------------


@companies_router.get(
    "/{company_id}/members",
    response_model=PaginationResponse[CompanyMemberDetailsResponse],
    status_code=status.HTTP_200_OK,
)
@cache(expire=300, key_builder=endpoint_key_builder)
async def get_company_members(
    member_service: CompanyMemberServiceDep,
    pagination: PaginationParamDep,
    company_id: UUID,
    role: CompanyRole | None = Query(default=None),
):
    company_members = await member_service.get_members_paginated(
        page=pagination.page,
        page_size=pagination.page_size,
        company_id=company_id,
        role=role,
    )
    return company_members


@companies_router.delete(
    "/{company_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_member(
    member_service: CompanyMemberServiceDep,
    acting_user: GetUserJWTDep,
    company_id: UUID,
    target_user_id: UUID,
):
    if acting_user.id == target_user_id:
        await member_service.leave_company(
            company_id=company_id, user_id=acting_user.id
        )
    else:
        await member_service.remove_member(
            company_id=company_id,
            acting_user_id=acting_user.id,
            target_user_id=target_user_id,
        )


@companies_router.patch(
    "/{company_id}/members/{target_user_id}",
    response_model=CompanyMemberDetailsResponse,
    status_code=status.HTTP_200_OK,
)
async def update_member_role(
    member_service: CompanyMemberServiceDep,
    acting_user: GetUserJWTDep,
    company_id: UUID,
    target_user_id: UUID,
    new_data: UpdateMemberRoleSchema,
):
    member = await member_service.update_role(
        company_id=company_id,
        target_user_id=target_user_id,
        acting_user_id=acting_user.id,
        new_role=new_data.role,
    )
    return member


@companies_router.get(
    "/{company_id}/members/{target_user_id}/stats",
    response_model=UserAverageCompanyStatsResponseSchema,
    status_code=status.HTTP_200_OK,
)
@cache(expire=3600, key_builder=endpoint_key_builder)
async def get_user_average_score_in_company(
    attempt_service: AttemptServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
    target_user_id: UUID,
):
    stats = await attempt_service.get_user_stats_in_company(
        company_id=company_id, acting_user_id=user.id, target_user_id=target_user_id
    )
    return stats
