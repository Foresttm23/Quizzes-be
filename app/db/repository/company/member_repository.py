from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository.base_repository import BaseRepository
from app.utils.enum_utils import CompanyRole
from db.models.company_models import Member as CompanyMemberModel


class MemberRepository(BaseRepository[CompanyMemberModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyMemberModel, db=db)

    async def get_company_role(
            self, company_id: UUID, user_id: UUID
    ) -> CompanyRole | None:
        query = select(self.model.role).where(
            self.model.company_id == company_id, self.model.user_id == user_id
        )
        role = await self.db.scalar(query)
        return role

    async def get_user_company_ids(self, user_id: UUID) -> Sequence[UUID]:
        query = select(self.model.company_id).where(self.model.user_id == user_id)
        user_company_ids = await self.db.scalars(query)
        return user_company_ids.all()

    async def get_and_lock_member_row(self, company_id: UUID, user_id: UUID) -> CompanyMemberModel | None:
        query = select(CompanyMemberModel).where(CompanyMemberModel.company_id == company_id,
                                                 CompanyMemberModel.user_id == user_id).with_for_update()
        member = await self.db.scalar(query)
        return member
