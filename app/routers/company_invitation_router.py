from typing import List
from uuid import UUID

from fastapi import APIRouter, status

from app.core.dependencies import GetUserJWTDep, CompanyInvitationServiceDep
from app.schemas.company_inv_req_schemas.company_inv_req_schema import InvitationDetailsResponse, \
    AcceptInvitationResponse

router = APIRouter(prefix="/company_invitations", tags=["Company Invitations"])


@router.post("/{company_id}/{invited_user_id}", response_model=InvitationDetailsResponse,
             status_code=status.HTTP_201_CREATED)
async def create_invitation_to_user(company_invitation_service: CompanyInvitationServiceDep, acting_user: GetUserJWTDep,
                                    company_id: UUID, invited_user_id: UUID):
    invitation = await company_invitation_service.send_invitation_to_user(company_id=company_id,
                                                                          invited_user_id=invited_user_id,
                                                                          acting_user_id=acting_user.id)
    return invitation


@router.patch("/accept/{invitation_id}", response_model=AcceptInvitationResponse, status_code=status.HTTP_200_OK)
async def accept_invitation_from_company(company_invitation_service: CompanyInvitationServiceDep,
                                         invited_user: GetUserJWTDep, invitation_id: UUID):
    invitation, new_member = await company_invitation_service.accept_invitation_from_company(
        invitation_id=invitation_id, invited_user_id=invited_user.id)
    return {"invitation": invitation, "new_member": new_member}


@router.patch("/decline/{invitation_id}", response_model=InvitationDetailsResponse, status_code=status.HTTP_200_OK)
async def decline_invitation_from_company(company_invitation_service: CompanyInvitationServiceDep,
                                          invited_user: GetUserJWTDep, invitation_id: UUID):
    invitation = await company_invitation_service.decline_invitation_from_company(invitation_id=invitation_id,
                                                                                  invited_user_id=invited_user.id)
    return invitation


@router.patch("/cancel/{invitation_id}", response_model=InvitationDetailsResponse, status_code=status.HTTP_200_OK)
async def cancel_invitation_from_company(company_invitation_service: CompanyInvitationServiceDep,
                                         acting_user: GetUserJWTDep, invitation_id: UUID):
    invitation = await company_invitation_service.cancel_invitation_by_company(invitation_id=invitation_id,
                                                                               acting_user_id=acting_user.id)
    return invitation


@router.get("/company/{company_id}/pending", response_model=List[InvitationDetailsResponse],
            status_code=status.HTTP_200_OK)
async def get_pending_invitations_for_company(company_invitation_service: CompanyInvitationServiceDep,
                                              acting_user: GetUserJWTDep, company_id: UUID):
    requests = await company_invitation_service.get_pending_invitations_for_company(company_id=company_id,
                                                                                    acting_user_id=acting_user.id)
    return requests


@router.get("/user/pending", response_model=List[InvitationDetailsResponse], status_code=status.HTTP_200_OK)
async def get_pending_invitations_for_user(company_invitation_service: CompanyInvitationServiceDep,
                                           user: GetUserJWTDep):
    requests = await company_invitation_service.get_pending_invitations_for_user(user_id=user.id)
    return requests
