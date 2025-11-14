from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CompanyPermissionException
from app.core.logger import logger
from app.db.models.company_member_model import CompanyMember as CompanyMemberModel
from app.db.models.company_model import Company as CompanyModel
from app.db.models.user_model import User as UserModel
from app.db.repository.company_member_repository import CompanyMemberRepository
from app.db.repository.company_repository import CompanyRepository
from app.schemas.company_schemas.company_request_schema import CompanyCreateRequest, CompanyUpdateInfoRequest
from app.schemas.company_schemas.company_response_schema import CompanyDetailsResponse
from app.services.base_service import BaseService
from app.services.user_service import UserService
from app.utils.enum_utils import CompanyRole


class CompanyService(BaseService[CompanyRepository]):
    @property
    def display_name(self) -> str:
        return "Company"

    def __init__(self, db: AsyncSession, user_service: UserService):
        super().__init__(repo=CompanyRepository(db=db))
        self.user_service = user_service
        self.member_repo = CompanyMemberRepository(db=db)

    # Later we can add filter fields to access only the specific companies.
    async def fetch_companies_data_paginated(self, page: int, page_size: int) -> dict[
        Any, list[CompanyDetailsResponse]]:
        companies_data = await self.repo.get_instances_data_paginated(page=page, page_size=page_size)
        return companies_data

    async def fetch_company_by_id(self, company_id: UUID) -> CompanyModel:
        company: CompanyModel = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=company_id)
        return company

    async def create_company(self, user: UserModel, company_info: CompanyCreateRequest):
        """Creates a new Company"""
        company_data = company_info.model_dump()
        company = CompanyModel(id=uuid4(), **company_data)

        owner_member = CompanyMemberModel(
            company_id=company.id,
            user_id=user.id,
            role=CompanyRole.OWNER
        )

        logger.info(f"Created new Company: {company.id} owner {owner_member.user_id}")

        await self.repo.save_changes_and_refresh(company, owner_member)

        return company

    async def update_company(self, company_id: UUID, user: UserModel,
                             company_info: CompanyUpdateInfoRequest) -> CompanyModel:
        company: CompanyModel = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=company_id)
        await self._ensure_user_has_role(user=user, company_id=company.id, role=CompanyRole.OWNER)

        company = await self._update_instance(instance=company, new_data=company_info)
        return company

    async def delete_company(self, company_id: UUID, user: UserModel):
        company: CompanyModel = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=company_id)
        await self._ensure_user_has_role(user=user, company_id=company.id, role=CompanyRole.OWNER)

        await self._delete_instance(instance=company)

    async def _ensure_user_has_role(self, user: UserModel, company_id: UUID, role: CompanyRole) -> None:
        users_with_role = await self.member_repo.get_members_by_role(company_id=company_id, role=role)

        if not any(u.user_id == user.id for u in users_with_role):
            raise CompanyPermissionException()
