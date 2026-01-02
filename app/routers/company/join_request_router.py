from uuid import UUID

from fastapi import APIRouter, status, Query

from app.core.config import settings
from app.core.dependencies import GetUserJWTDep, CompanyJoinRequestServiceDep
from app.schemas.base_schemas import PaginationResponse
from schemas.company.inv_req_schema import RequestDetailsResponse, AcceptRequestResponse

router = APIRouter(prefix="/company-join-requests", tags=["Company Join Requests"])


@router.post("/{company_id}", response_model=RequestDetailsResponse, status_code=status.HTTP_200_OK)
async def create_company_request(company_join_request_service: CompanyJoinRequestServiceDep, user: GetUserJWTDep,
                                 company_id: UUID):
    request = await company_join_request_service.create_join_request(company_id=company_id, requesting_user_id=user.id)
    return request


@router.patch("/{request_id}/accept", response_model=AcceptRequestResponse, status_code=status.HTTP_200_OK)
async def accept_request(company_join_request_service: CompanyJoinRequestServiceDep, acting_user: GetUserJWTDep,
                         request_id: UUID):
    request, new_member = await company_join_request_service.accept_request(request_id=request_id,
                                                                            acting_user_id=acting_user.id)
    return {"request": request, "new_member": new_member}


@router.patch("/{request_id}/decline", response_model=RequestDetailsResponse, status_code=status.HTTP_200_OK)
async def decline_request(company_join_request_service: CompanyJoinRequestServiceDep, acting_user: GetUserJWTDep,
                          request_id: UUID):
    request = await company_join_request_service.decline_request(request_id=request_id, acting_user_id=acting_user.id)
    return request


@router.patch("/{request_id}/cancel", response_model=RequestDetailsResponse, status_code=status.HTTP_200_OK)
async def cancel_request(company_join_request_service: CompanyJoinRequestServiceDep, requesting_user: GetUserJWTDep,
                         request_id: UUID):
    request = await company_join_request_service.cancel_request(request_id=request_id,
                                                                requesting_user_id=requesting_user.id)
    return request


@router.get("/company/{company_id}/pending", response_model=PaginationResponse[RequestDetailsResponse],
            status_code=status.HTTP_200_OK)
async def get_pending_requests_for_company(company_join_request_service: CompanyJoinRequestServiceDep,
                                           acting_user: GetUserJWTDep, company_id: UUID,
                                           page: int = Query(default=1, ge=1),
                                           page_size: int = Query(default=10, ge=1, le=settings.APP.MAX_PAGE_SIZE)):
    requests = await company_join_request_service.get_pending_for_company(company_id=company_id,
                                                                          acting_user_id=acting_user.id, page=page,
                                                                          page_size=page_size)
    return requests


@router.get("/user/pending", response_model=PaginationResponse[RequestDetailsResponse], status_code=status.HTTP_200_OK)
async def get_pending_requests_for_user(company_join_request_service: CompanyJoinRequestServiceDep, user: GetUserJWTDep,
                                        page: int = Query(default=1, ge=1),
                                        page_size: int = Query(default=10, ge=1, le=settings.APP.MAX_PAGE_SIZE)):
    requests = await company_join_request_service.get_pending_for_user(user_id=user.id, page=page, page_size=page_size)
    return requests
