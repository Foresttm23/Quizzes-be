from uuid import UUID

from fastapi import APIRouter, status, Query

from app.core.config import settings
from app.core.dependencies import CompanyMemberServiceDep
from app.core.dependencies import GetUserJWTDep
from app.schemas.base_schemas import PaginationResponse
from app.schemas.company_members_schemas.company_member_response_schema import CompanyMemberDetailsResponse

router = APIRouter(prefix="/company_members", tags=["Company Members"])


@router.get("/{company_id}", response_model=PaginationResponse[CompanyMemberDetailsResponse],
            status_code=status.HTTP_200_OK)
async def list_company_members(company_member_service: CompanyMemberServiceDep, company_id: UUID,
                               page: int = Query(ge=1), page_size: int = Query(ge=1, le=settings.APP.MAX_PAGE_SIZE)):
    company_members = company_member_service.get_members_paginated(page=page, page_size=page_size,
                                                                   company_id=company_id)
    return company_members


@router.delete("/{company_id}/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_company(company_member_service: CompanyMemberServiceDep, acting_user: GetUserJWTDep,
                                   company_id: UUID, user_id: UUID):
    await company_member_service.remove_user_from_company(company_id=company_id, acting_user_id=acting_user.id,
                                                          user_id=user_id)


@router.delete("/{company_id}/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_company(company_member_service: CompanyMemberServiceDep, user: GetUserJWTDep, company_id: UUID):
    await company_member_service.leave_company(company_id=company_id, user_id=user.id)
