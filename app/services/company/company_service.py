from typing import Sequence
from typing import TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.exceptions import InstanceNotFoundException
from app.core.logger import logger
from app.db.models.company.company_model import Company as CompanyModel
from app.db.models.company.member_model import Member as CompanyMemberModel
from app.schemas.base_schemas import PaginationResponse
from app.schemas.company_schemas.company_request_schema import CompanyCreateRequest, CompanyUpdateInfoRequest
from app.services.base_service import BaseService
from app.utils.enum_utils import CompanyRole
from db.repository.company.company_repository import CompanyRepository
from services.company.company_member_service import CompanyMemberService

SchemaType = TypeVar("SchemaType", bound=BaseModel)


class CompanyService(BaseService[CompanyRepository]):
    @property
    def display_name(self) -> str:
        return "Company"

    def __init__(self, db: AsyncSession, company_member_service: CompanyMemberService):
        super().__init__(repo=CompanyRepository(db=db))
        self.company_member_service = company_member_service

    async def get_companies_paginated(self, page: int, page_size: int, user_id: UUID | None = None) -> \
            PaginationResponse[SchemaType]:
        if not user_id:
            return await self._get_visible_companies_paginated(page=page, page_size=page_size)

        user_company_ids = await self.company_member_service.get_user_company_ids(user_id=user_id)

        if not user_company_ids:
            return await self._get_visible_companies_paginated(page=page, page_size=page_size)

        return await self._get_visible_and_user_companies_paginated(page=page, page_size=page_size,
                                                                    user_company_ids=user_company_ids)

    async def _get_visible_companies_paginated(self, page: int, page_size: int):
        filters = {CompanyModel.is_visible: True}
        return await self.repo.get_instances_data_paginated(page=page, page_size=page_size, filters=filters)

    async def _get_visible_and_user_companies_paginated(self, page: int, page_size: int,
                                                        user_company_ids: Sequence[UUID]):
        condition = or_(CompanyModel.is_visible.is_(True), CompanyModel.id.in_(user_company_ids))

        stmt = select(CompanyModel).where(condition)
        stmt = stmt.order_by(CompanyModel.id.desc())

        return await self.repo.paginate_query(stmt, page, page_size)

    async def get_by_id(self, company_id: UUID, user_id: UUID | None = None) -> CompanyModel:
        company = await self.get_company(company_id=company_id)
        if company.is_visible:
            return company

        # Invisible company then check if user is a part of it
        if not user_id:
            raise InstanceNotFoundException()

        await self.company_member_service.assert_user_in_company(company_id=company_id, user_id=user_id)
        return company

    async def create_company(self, acting_user_id: UUID, company_info: CompanyCreateRequest):
        """Creates a new Company"""
        company_data = company_info.model_dump()
        company = CompanyModel(id=uuid4(), **company_data)

        owner_member = CompanyMemberModel(company_id=company.id, user_id=acting_user_id, role=CompanyRole.OWNER)

        logger.info(f"Created new Company: {company.id} owner {owner_member.user_id}")

        await self.repo.save_and_refresh(company, owner_member)

        return company

    async def update_company(self, company_id: UUID, acting_user_id: UUID,
                             company_info: CompanyUpdateInfoRequest) -> CompanyModel:
        company = await self.get_company(company_id=company_id)
        acting_user_role = await self.company_member_service.repo.get_company_role(company_id=company.id,
                                                                                   user_id=acting_user_id)
        self.company_member_service.assert_user_has_permissions(user_role=acting_user_role,
                                                                required_role=CompanyRole.ADMIN)

        company = await self._update_instance(instance=company, new_data=company_info)
        await self.repo.save_and_refresh(company)

        return company

    async def delete_company(self, company_id: UUID, acting_user_id: UUID):
        company = await self.get_company(company_id=company_id)
        acting_user_role = await self.company_member_service.repo.get_company_role(company_id=company.id,
                                                                                   user_id=acting_user_id)
        self.company_member_service.assert_user_has_permissions(user_role=acting_user_role,
                                                                required_role=CompanyRole.OWNER)

        await self._delete_instance(instance=company)
        await self.repo.commit()

    async def get_company(self, company_id: UUID,
                          relationships: set[InstrumentedAttribute] | None = None) -> CompanyModel:
        company = await self.repo.get_instance_by_field_or_none(CompanyModel.id, value=company_id,
                                                                relationships=relationships)
        if not company:
            raise InstanceNotFoundException(instance_name=self.display_name)
        return company
