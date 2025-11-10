from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CompanyPermissionException
from app.core.logger import logger
from app.db.models.company_model import Company as CompanyModel
from app.db.repository.company_repository import CompanyRepository
from app.schemas.company_schemas.company_request_schema import CompanyCreateRequest, CompanyUpdateInfoRequest
from app.schemas.company_schemas.company_response_schema import CompanyDetailsResponse
from app.services.base_service import BaseService
from app.services.user_service import UserService


class CompanyService(BaseService[CompanyRepository]):
    @property
    def display_name(self) -> str:
        return "Company"

    def __init__(self, db: AsyncSession, user_service: UserService):
        super().__init__(repo=CompanyRepository(db=db))
        self.user_service = user_service

    # Later we can add filter fields to access only the specific companies.
    async def fetch_companies_data_paginated(self, page: int, page_size: int) -> dict[
        Any, list[CompanyDetailsResponse]]:
        companies_data = await super()._fetch_instances_data_paginated(page=page, page_size=page_size)
        return companies_data

    async def fetch_company_by_id(self, company_id: UUID) -> CompanyModel:
        company = await super()._fetch_instance(field_name="id", field_value=company_id)
        return company

    async def create_company(self, owner_email: str, company_info: CompanyCreateRequest):
        """Creates a new Company"""
        owner = await self.user_service.fetch_user("email", owner_email)
        company_data = company_info.model_dump()
        company = CompanyModel(**company_data, owner_id=owner.id)

        await self.repo.save_changes_and_refresh(instance=company)
        logger.info(f"Created new Company: {company.id} owner {owner_email}")

        return company

    async def update_company(self, company_id: UUID, owner_email: str,
                             company_info: CompanyUpdateInfoRequest) -> CompanyModel:
        company: CompanyModel = await super()._fetch_instance(field_name="id", field_value=company_id)
        owner = await self.user_service.fetch_user("email", owner_email)

        if company.owner_id != owner.id:
            raise CompanyPermissionException()

        company = await super()._update_instance(instance=company, new_data=company_info)
        return company

    async def delete_company(self, company_id: UUID, owner_email: str):
        company: CompanyModel = await super()._fetch_instance(field_name="id", field_value=company_id)
        owner = await self.user_service.fetch_user("email", owner_email)
        if company.owner_id != owner.id:
            raise CompanyPermissionException()

        await super()._delete_instance(instance=company)
