from typing import Sequence
from uuid import UUID

from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company_join_requests_model import CompanyJoinRequest as CompanyJoinRequestModel
from app.db.repository.base_repository import BaseRepository
from app.utils.enum_utils import MessageStatus


class CompanyJoinRequestRepository(BaseRepository[CompanyJoinRequestModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyJoinRequestModel, db=db)
        self.model = CompanyJoinRequestModel

    async def get_pending_requests_for_company(self, company_id: UUID) -> Sequence[CompanyJoinRequestModel]:
        """
        For company.
        Returns a list of pending membership requests from users.
        :param company_id:
        :return:
        """
        query = select(self.model).where(self.model.company_id == company_id,
                                         self.model.status == MessageStatus.PENDING)
        requests = await self._execute_base_request(query=query)
        return requests

    async def get_pending_requests_for_user(self, user_id: UUID) -> Sequence[CompanyJoinRequestModel]:
        """
        For user.
        Returns a list of pending user requests to a companies.
        :param user_id:
        :return:
        """
        query = select(self.model).where(self.model.requesting_user_id == user_id,
                                         self.model.status == MessageStatus.PENDING)
        requests = await self._execute_base_request(query=query)
        return requests

    async def _execute_base_request(self, query: Select) -> Sequence[CompanyJoinRequestModel]:
        requests = await self.db.scalars(query)
        return requests.all()
