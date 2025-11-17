from typing import Sequence
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company_member_model import CompanyMember as CompanyMemberModel
from app.utils.enum_utils import CompanyRole
from .base_repository import BaseRepository


class CompanyMemberRepository(BaseRepository[CompanyMemberModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyMemberModel, db=db)

    async def get_user_role(self, company_id: UUID, user_id: UUID) -> CompanyRole | None:
        query = (select(self.model.role).where(self.model.company_id == company_id, self.model.user_id == user_id))
        result = await self.db.execute(query)
        role = result.scalar_one_or_none()

        return role

    async def get_user_company_ids(self, user_id: UUID) -> Sequence[UUID]:
        query = select(self.model.company_id).where(self.model.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user_from_company(self, company_id: UUID, user_id: UUID) -> None:
        query = select(self.model).where(self.model.user_id == user_id, self.model.company_id == company_id)
        result = await self.db.execute(query)
        company_member = result.scalar_one_or_none()
        return company_member

    async def remove_user_from_company(self, company_id: UUID, user_id: UUID):
        query = delete(self.model).where(self.model.company_id == company_id, self.model.user_id == user_id)
        await self.db.execute(query)
