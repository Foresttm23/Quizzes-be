from typing import Sequence
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidRecipientException
from app.db.models.company_join_requests_model import CompanyJoinRequest as CompanyJoinRequestModel
from app.db.models.company_member_model import CompanyMember as CompanyMemberModel
from app.db.repository.company_join_request_repository import CompanyJoinRequestRepository
from app.schemas.company_inv_req_schemas.company_inv_req_schema import UpdateRequestSchema
from app.services.base_service import BaseService
from app.services.company_member_service import CompanyMemberService
from app.utils.enum_utils import MessageStatus, CompanyRole


class CompanyJoinRequestService(BaseService[CompanyJoinRequestRepository]):
    @property
    def display_name(self) -> str:
        return "JoinRequest"

    def __init__(self, db: AsyncSession, company_member_service: CompanyMemberService):
        super().__init__(repo=CompanyJoinRequestRepository(db=db))
        self.company_member_service = company_member_service

    async def create_request_to_company(self, company_id: UUID, requesting_user_id: UUID) -> CompanyJoinRequestModel:
        """
        Creates request from user to a desired company.
        :param company_id:
        :param requesting_user_id: is the same as user.id from JWT token
        :return: request
        """
        await self.company_member_service.assert_user_not_in_company(company_id=company_id, user_id=requesting_user_id)
        new_request = CompanyJoinRequestModel(id=uuid4(), company_id=company_id, requesting_user_id=requesting_user_id)
        await self.repo.save_changes_and_refresh(new_request)

        return new_request

    async def accept_request_from_user(self, request_id: UUID, acting_user_id: UUID) -> tuple[
        CompanyJoinRequestModel, CompanyMemberModel]:
        """
        Accepts request from user by a company.
        :param request_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: request, new_member
        """
        request = await self._get_request_and_assert_role(request_id=request_id, acting_user_id=acting_user_id)

        new_request_data = UpdateRequestSchema(request_status=MessageStatus.ACCEPTED)
        await self._update_instance(instance=request, new_data=new_request_data)

        new_member = CompanyMemberModel(company_id=request.company_id, user_id=request.requesting_user_id)
        await self.repo.save_changes_and_refresh(request, new_member)

        return request, new_member

    async def decline_request_from_user(self, request_id: UUID, acting_user_id: UUID) -> CompanyJoinRequestModel:
        """
        Decline request from user by a company.
        :param request_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: request
        """
        request = await self._get_request_and_assert_role(request_id=request_id, acting_user_id=acting_user_id)

        new_request_data = UpdateRequestSchema(request_status=MessageStatus.DECLINED)
        await self._update_instance(instance=request, new_data=new_request_data)
        await self.repo.save_changes_and_refresh(request)

        return request

    async def cancel_request_by_user(self, request_id: UUID, requesting_user_id: UUID) -> CompanyJoinRequestModel:
        """
        Cancels request to company by a user.
        :param request_id:
        :param requesting_user_id: id of a user with admin or higher role in a company
        :return: request
        """
        request = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=request_id)
        if request.requesting_user_id != requesting_user_id:
            raise InvalidRecipientException()

        new_request_data = UpdateRequestSchema(request_status=MessageStatus.CANCELED)
        await self._update_instance(instance=request, new_data=new_request_data)
        await self.repo.save_changes_and_refresh(request)

        return request

    async def get_pending_requests_for_company(self, company_id: UUID, acting_user_id: UUID) -> Sequence[
        CompanyJoinRequestModel]:
        await self.company_member_service.assert_user_has_role(company_id=company_id, user_id=acting_user_id,
                                                               required_role=CompanyRole.ADMIN)
        requests = await self.repo.get_pending_requests_for_company(company_id=company_id)
        return requests

    async def get_pending_requests_for_user(self, user_id: UUID) -> Sequence[CompanyJoinRequestModel]:
        requests = await self.repo.get_pending_requests_for_user(user_id=user_id)
        return requests

    async def _get_request_and_assert_role(self, request_id: UUID, acting_user_id: UUID) -> CompanyJoinRequestModel:
        """
        Helper method to get request and verify acting_user_id as Admin or higher role.
        :param request_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: request
        """
        request = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=request_id)
        await self.company_member_service.assert_user_has_role(company_id=request.company_id, user_id=acting_user_id,
                                                               required_role=CompanyRole.ADMIN)
        return request
