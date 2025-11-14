from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company_member_model import CompanyMember as CompanyMemberModel
from app.utils.enum_utils import CompanyRole
from .base_repository import BaseRepository


class CompanyMemberRepository(BaseRepository[CompanyMemberModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyMemberModel, db=db)

    async def get_members_by_role(self, company_id: UUID, role: CompanyRole) -> Sequence[CompanyMemberModel]:
        query = select(self.model).where(self.model.company_id == company_id, (self.model.role == role))
        result = await self.db.execute(query)

        instances = result.scalars().all()
        return instances
