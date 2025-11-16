from typing import Any, Sequence
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InstanceNotFoundException
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

    async def fetch_companies_data_paginated(self, page: int, page_size: int, user_id: UUID | None = None) -> dict[
        Any, list[CompanyDetailsResponse]]:

        if not user_id:
            return await self._fetch_visible_companies_paginated(page=page, page_size=page_size)

        user_company_ids = await self.member_repo.get_user_company_ids(user_id=user_id)

        if not user_company_ids:
            return await self._fetch_visible_companies_paginated(page=page, page_size=page_size)

        return await self._fetch_visible_and_user_companies_paginated(page=page, page_size=page_size,
                                                                      user_company_ids=user_company_ids)

    async def _fetch_visible_companies_paginated(self, page: int, page_size: int):
        filters = {"is_visible": True}
        return await self.repo.get_instances_data_paginated(page=page, page_size=page_size, filters=filters)

    async def _fetch_visible_and_user_companies_paginated(self, page: int, page_size: int,
                                                          user_company_ids: Sequence[UUID]):
        filters = {"__or__": [{"is_visible": True}, {"id__in": user_company_ids}]}
        return await self.repo.get_instances_data_paginated(page=page, page_size=page_size, filters=filters)

    async def fetch_company_by_id(self, company_id: UUID, user_id: UUID | None = None) -> CompanyModel:
        company: CompanyModel = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=company_id)

        if company.is_visible:
            return company

        # Invisible company then check if user is a part of it
        if not user_id:
            raise InstanceNotFoundException()

        await self.member_repo.assert_user_in_company(company_id=company_id, user_id=user_id)
        return company

    async def create_company(self, user: UserModel, company_info: CompanyCreateRequest):
        """Creates a new Company"""
        company_data = company_info.model_dump()
        company = CompanyModel(id=uuid4(), **company_data)

        owner_member = CompanyMemberModel(company_id=company.id, user_id=user.id, role=CompanyRole.OWNER)

        logger.info(f"Created new Company: {company.id} owner {owner_member.user_id}")

        await self.repo.save_changes_and_refresh(company, owner_member)

        return company

    async def update_company(self, company_id: UUID, user: UserModel,
                             company_info: CompanyUpdateInfoRequest) -> CompanyModel:
        company: CompanyModel = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=company_id)
        await self.member_repo.assert_user_has_role(company_id=company_id, user_id=user.id,
                                                    required_role=CompanyRole.OWNER)

        company = await self._update_instance(instance=company, new_data=company_info)
        return company

    async def delete_company(self, company_id: UUID, user: UserModel):
        company: CompanyModel = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=company_id)
        await self.member_repo.assert_user_has_role(company_id=company_id, user_id=user.id,
                                                    required_role=CompanyRole.OWNER)

        await self._delete_instance(instance=company)
