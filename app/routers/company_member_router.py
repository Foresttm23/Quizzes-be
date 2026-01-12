from uuid import UUID

from fastapi import APIRouter, status, Query

from app.core.config import settings
from app.core.dependencies import CompanyMemberServiceDep
from app.core.dependencies import GetUserJWTDep
from app.schemas.base_schemas import PaginationResponse
from app.schemas.company_members_schemas.company_member_response_schema import CompanyMemberDetailsResponse
from app.schemas.company_members_schemas.company_member_response_schema import UpdateMemberRoleSchema
from utils.enum_utils import CompanyRole

router = APIRouter(prefix="/company-members", tags=["Company Members"])


@router.get("/{company_id}", response_model=PaginationResponse[CompanyMemberDetailsResponse],
            status_code=status.HTTP_200_OK)
async def get_members_paginated(company_member_service: CompanyMemberServiceDep, company_id: UUID,
                                role: CompanyRole | None = Query(default=None), page: int = Query(default=1, ge=1),
                                page_size: int = Query(default=10, ge=1, le=settings.APP.MAX_PAGE_SIZE)):
    company_members = company_member_service.get_members_paginated(page=page, page_size=page_size,
                                                                   company_id=company_id, role=role)
    return company_members


@router.delete("/{company_id}/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(company_member_service: CompanyMemberServiceDep, acting_user: GetUserJWTDep, company_id: UUID,
                        target_user_id: UUID):
    if acting_user.id == target_user_id:
        await company_member_service.leave_company(company_id=company_id, user_id=acting_user.id)
    else:
        await company_member_service.remove_member(company_id=company_id, acting_user_id=acting_user.id,
                                                   target_user_id=target_user_id)


@router.patch("/{company_id}/{target_user_id}", response_model=CompanyMemberDetailsResponse,
              status_code=status.HTTP_200_OK)
async def update_member_role(company_member_service: CompanyMemberServiceDep, acting_user: GetUserJWTDep,
                             company_id: UUID, target_user_id: UUID, new_data: UpdateMemberRoleSchema):
    member = await company_member_service.update_role(company_id=company_id, target_user_id=target_user_id,
                                                      acting_user_id=acting_user.id, new_role=new_data.role)
    return member
