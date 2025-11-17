from typing import List
from uuid import UUID

from fastapi import APIRouter, status

from app.core.dependencies import GetUserJWTDep, CompanyJoinRequestServiceDep
from app.schemas.company_inv_req_schemas.company_inv_req_schema import RequestDetailsResponse, AcceptRequestResponse

router = APIRouter(prefix="/company_join_requests", tags=["Company Join Requests"])


@router.post("/{company_id}", response_model=RequestDetailsResponse, status_code=status.HTTP_200_OK)
async def create_company_request(company_join_request_service: CompanyJoinRequestServiceDep, user: GetUserJWTDep,
                                 company_id: UUID):
    request = await company_join_request_service.create_request_to_company(company_id=company_id,
                                                                           requesting_user_id=user.id)
    return request


@router.patch("/accept/{request_id}", response_model=AcceptRequestResponse, status_code=status.HTTP_200_OK)
async def accept_request_from_user(company_join_request_service: CompanyJoinRequestServiceDep,
                                   acting_user: GetUserJWTDep, request_id: UUID):
    request, new_member = await company_join_request_service.accept_request_from_user(request_id=request_id,
                                                                                      acting_user_id=acting_user.id)
    return {"request": request, "new_member": new_member}


@router.patch("/decline/{request_id}", response_model=RequestDetailsResponse, status_code=status.HTTP_200_OK)
async def decline_request_from_user(company_join_request_service: CompanyJoinRequestServiceDep,
                                    acting_user: GetUserJWTDep, request_id: UUID):
    request = await company_join_request_service.decline_request_from_user(request_id=request_id,
                                                                           acting_user_id=acting_user.id)
    return request


@router.patch("/cancel/{request_id}", response_model=RequestDetailsResponse, status_code=status.HTTP_200_OK)
async def cancel_request_from_user(company_join_request_service: CompanyJoinRequestServiceDep,
                                   requesting_user: GetUserJWTDep, request_id: UUID):
    request = await company_join_request_service.cancel_request_by_user(request_id=request_id,
                                                                        requesting_user_id=requesting_user.id)
    return request


@router.get("/company/{company_id}/pending", response_model=List[RequestDetailsResponse],
            status_code=status.HTTP_200_OK)
async def get_pending_requests_for_company(company_join_request_service: CompanyJoinRequestServiceDep,
                                           acting_user: GetUserJWTDep, company_id: UUID):
    requests = await company_join_request_service.get_pending_requests_for_company(company_id=company_id,
                                                                                   acting_user_id=acting_user.id)
    return requests


@router.get("/user/pending", response_model=List[RequestDetailsResponse], status_code=status.HTTP_200_OK)
async def get_pending_requests_for_user(company_join_request_service: CompanyJoinRequestServiceDep,
                                        user: GetUserJWTDep):
    requests = await company_join_request_service.get_pending_requests_for_user(user_id=user.id)
    return requests
