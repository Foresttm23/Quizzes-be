from typing import Sequence
from uuid import UUID

from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company_invitations_model import CompanyInvitation as CompanyInvitationModel
from app.db.repository.base_repository import BaseRepository
from app.utils.enum_utils import MessageStatus


class CompanyInvitationRepository(BaseRepository[CompanyInvitationModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyInvitationModel, db=db)
        self.model = CompanyInvitationModel

    async def get_pending_invitations_for_user(self, user_id: UUID) -> Sequence[CompanyInvitationModel]:
        """
        For user.
        Returns a list of received invitations from companies.
        :param user_id:
        :return:
        """
        query = select(self.model).where(self.model.invited_user_id == user_id,
                                         self.model.status == MessageStatus.PENDING)
        invitations = await self._execute_base_invitation(query=query)
        return invitations

    async def get_pending_invitations_for_company(self, company_id: UUID) -> Sequence[CompanyInvitationModel]:
        """
        For company.
        Returns a list of sent invitations to users.
        :param company_id:
        :return:
        """
        query = select(self.model).where(self.model.company_id == company_id,
                                         self.model.status == MessageStatus.PENDING)
        invitations = await self._execute_base_invitation(query=query)
        return invitations

    async def _execute_base_invitation(self, query: Select) -> Sequence[CompanyInvitationModel]:
        result = await self.db.execute(query)
        return result.scalars().all()
