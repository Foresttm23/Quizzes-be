from typing import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import BaseRepository
from .enums import CompanyRole
from .models import (
    Company as CompanyModel,
)
from .models import (
    Invitation as CompanyInvitationModel,
)
from .models import (
    JoinRequest as CompanyJoinRequestModel,
)
from .models import (
    Member as CompanyMemberModel,
)


class JoinRequestRepository(BaseRepository[CompanyJoinRequestModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyJoinRequestModel, db=db)


class InvitationRepository(BaseRepository[CompanyInvitationModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyInvitationModel, db=db)


class CompanyRepository(BaseRepository[CompanyModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyModel, db=db)


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

    async def get_and_lock_member_row(
        self, company_id: UUID, user_id: UUID
    ) -> CompanyMemberModel | None:
        query = (
            select(CompanyMemberModel)
            .where(
                CompanyMemberModel.company_id == company_id,
                CompanyMemberModel.user_id == user_id,
            )
            .with_for_update()
        )
        member = await self.db.scalar(query)
        return member

    async def get_members_count_by_ids(self, company_id: UUID, *args: UUID) -> int:
        query = (
            select(func.count(CompanyMemberModel.user_id))
            .where(CompanyMemberModel.company_id == company_id)
            .where(CompanyMemberModel.user_id.in_(args))
        )

        members_count = await self.db.scalar(query)
        return members_count or 0
