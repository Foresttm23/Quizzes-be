from uuid import UUID

from fastapi import APIRouter, status, Query

from app.core.config import settings
from app.core.dependencies import GetUserJWTDep, CompanyInvitationServiceDep
from app.schemas.base_schemas import PaginationResponse
from schemas.company.inv_req_schema import InvitationDetailsResponse, \
    AcceptInvitationResponse, CreateInvitationRequest

router = APIRouter(prefix="/company-invitations", tags=["Company Invitations"])


@router.post("/{company_id}", response_model=InvitationDetailsResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(company_invitation_service: CompanyInvitationServiceDep, acting_user: GetUserJWTDep,
                            company_id: UUID, request_data: CreateInvitationRequest):
    invitation = await company_invitation_service.create_invitation(company_id=company_id,
                                                                    invited_user_id=request_data.invited_user_id,
                                                                    acting_user_id=acting_user.id)

    return invitation


@router.patch("/{invitation_id}/accept", response_model=AcceptInvitationResponse, status_code=status.HTTP_200_OK)
async def accept_invitation(company_invitation_service: CompanyInvitationServiceDep, invited_user: GetUserJWTDep,
                            invitation_id: UUID):
    invitation, new_member = await company_invitation_service.accept_from_company(invitation_id=invitation_id,
                                                                                  invited_user_id=invited_user.id)
    return {"invitation": invitation, "new_member": new_member}


@router.patch("/{invitation_id}/decline", response_model=InvitationDetailsResponse, status_code=status.HTTP_200_OK)
async def decline_invitation(company_invitation_service: CompanyInvitationServiceDep, invited_user: GetUserJWTDep,
                             invitation_id: UUID):
    invitation = await company_invitation_service.decline_from_company(invitation_id=invitation_id,
                                                                       invited_user_id=invited_user.id)
    return invitation


@router.patch("/{invitation_id}/cancel", response_model=InvitationDetailsResponse, status_code=status.HTTP_200_OK)
async def cancel_invitation(company_invitation_service: CompanyInvitationServiceDep, acting_user: GetUserJWTDep,
                            invitation_id: UUID):
    invitation = await company_invitation_service.cancel_by_company(invitation_id=invitation_id,
                                                                    acting_user_id=acting_user.id)
    return invitation


@router.get("/company/{company_id}/pending", response_model=PaginationResponse[InvitationDetailsResponse],
            status_code=status.HTTP_200_OK)
async def get_company_pending_invitations(company_invitation_service: CompanyInvitationServiceDep,
                                          acting_user: GetUserJWTDep,
                                          company_id: UUID, page: int = Query(default=1, ge=1),
                                          page_size: int = Query(default=10, ge=1, le=settings.APP.MAX_PAGE_SIZE)):
    requests = await company_invitation_service.get_pending_for_company(company_id=company_id,
                                                                        acting_user_id=acting_user.id, page=page,
                                                                        page_size=page_size)
    return requests


@router.get("/user/pending", response_model=PaginationResponse[InvitationDetailsResponse],
            status_code=status.HTTP_200_OK)
async def get_user_pending_invitations(company_invitation_service: CompanyInvitationServiceDep,
                                       user: GetUserJWTDep, page: int = Query(default=1, ge=1),
                                       page_size: int = Query(default=10, ge=1, le=settings.APP.MAX_PAGE_SIZE)):
    requests = await company_invitation_service.get_pending_for_user(user_id=user.id, page=page, page_size=page_size)
    return requests
