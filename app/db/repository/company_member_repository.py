from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CompanyPermissionException, UserIsNotACompanyMemberException, InstanceNotFoundException
from app.db.models.company_member_model import CompanyMember as CompanyMemberModel
from app.utils.enum_utils import CompanyRole
from .base_repository import BaseRepository


class CompanyMemberRepository(BaseRepository[CompanyMemberModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyMemberModel, db=db)

    async def assert_user_has_role(self, company_id: UUID, user_id: UUID,
                                   required_role: CompanyRole) -> CompanyRole | None:
        query = (select(self.model.role).where(self.model.company_id == company_id, self.model.user_id == user_id))
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()

        if role is None:
            raise UserIsNotACompanyMemberException()

        if role < required_role:
            raise CompanyPermissionException()

    async def get_user_company_ids(self, user_id: UUID) -> Sequence[UUID]:
        query = select(self.model.company_id).where(self.model.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def assert_user_in_company(self, company_id: UUID, user_id: UUID):
        query = select(self.model.company_id).where(self.model.user_id == user_id)
        result = await self.db.execute(query)
        if not result.scalar():
            raise InstanceNotFoundException("User")
