from typing import Sequence
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company.member_model import Member as CompanyMemberModel
from app.utils.enum_utils import CompanyRole
from .base_repository import BaseRepository


class CompanyMemberRepository(BaseRepository[CompanyMemberModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyMemberModel, db=db)

    async def get_company_role(self, company_id: UUID, user_id: UUID) -> CompanyRole | None:
        query = select(self.model.role).where(self.model.company_id == company_id, self.model.user_id == user_id)
        role = await self.db.scalar(query)
        return role

    async def get_user_company_ids(self, user_id: UUID) -> Sequence[UUID]:
        query = select(self.model.company_id).where(self.model.user_id == user_id)
        user_company_ids = await self.db.scalars(query)
        return user_company_ids.all()

    async def remove_member(self, company_id: UUID, user_id: UUID):
        query = delete(self.model).where(self.model.company_id == company_id, self.model.user_id == user_id)
        await self.db.execute(query)
