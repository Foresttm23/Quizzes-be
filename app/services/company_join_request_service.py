from typing import TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidRecipientException
from app.db.models.company.join_request_model import JoinRequest as CompanyJoinRequestModel
from app.db.models.company.member_model import Member as CompanyMemberModel
from app.db.repository.company_join_request_repository import CompanyJoinRequestRepository
from app.schemas.base_schemas import PaginationResponse
from app.schemas.company_inv_req_schemas.company_inv_req_schema import UpdateRequestSchema
from app.services.base_service import BaseService
from app.services.company_member_service import CompanyMemberService
from app.utils.enum_utils import MessageStatus, CompanyRole

SchemaType = TypeVar("SchemaType", bound=BaseModel)

class CompanyJoinRequestService(BaseService[CompanyJoinRequestRepository]):
    @property
    def display_name(self) -> str:
        return "JoinRequest"

    def __init__(self, db: AsyncSession, company_member_service: CompanyMemberService):
        super().__init__(repo=CompanyJoinRequestRepository(db=db))
        self.company_member_service = company_member_service

    async def create_join_request(self, company_id: UUID, requesting_user_id: UUID) -> CompanyJoinRequestModel:
        """
        Creates request from user to a desired company.
        :param company_id:
        :param requesting_user_id: is the same as user.id from JWT token
        :return: request
        """
        await self.company_member_service.assert_user_not_in_company(company_id=company_id, user_id=requesting_user_id)
        new_request = CompanyJoinRequestModel(id=uuid4(), company_id=company_id, requesting_user_id=requesting_user_id)

        await self.repo.save_and_refresh(new_request)
        return new_request

    async def accept_request(self, request_id: UUID, acting_user_id: UUID) -> tuple[
        CompanyJoinRequestModel, CompanyMemberModel]:
        """
        Accepts request from user by a company.
        :param request_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: request, new_member
        """
        request = await self._get_and_assert_role(request_id=request_id, acting_user_id=acting_user_id)

        new_request_data = UpdateRequestSchema(status=MessageStatus.ACCEPTED)
        request = await self._update_instance(instance=request, new_data=new_request_data)

        new_member = CompanyMemberModel(company_id=request.company_id, user_id=request.requesting_user_id)

        await self.repo.save_and_refresh(request, new_member)
        return request, new_member

    async def decline_request(self, request_id: UUID, acting_user_id: UUID) -> CompanyJoinRequestModel:
        """
        Decline request from user by a company.
        :param request_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: request
        """
        request = await self._get_and_assert_role(request_id=request_id, acting_user_id=acting_user_id)

        new_request_data = UpdateRequestSchema(status=MessageStatus.DECLINED)
        await self._update_instance(instance=request, new_data=new_request_data)

        await self.repo.save_and_refresh(request)
        return request

    async def cancel_request(self, request_id: UUID, requesting_user_id: UUID) -> CompanyJoinRequestModel:
        """
        Cancels request to company by a user.
        :param request_id:
        :param requesting_user_id: id of a user with admin or higher role in a company
        :return: request
        """
        request = await self.repo.get_instance_by_field_or_404(CompanyJoinRequestModel.id, value=request_id)
        if request.requesting_user_id != requesting_user_id:
            raise InvalidRecipientException()

        new_request_data = UpdateRequestSchema(status=MessageStatus.CANCELED)
        await self._update_instance(instance=request, new_data=new_request_data)

        await self.repo.save_and_refresh(request)
        return request

    async def get_pending_for_company(self, company_id: UUID, acting_user_id: UUID, page: int = 1,
                                      page_size: int = 100) -> PaginationResponse[SchemaType]:
        await self.company_member_service.assert_user_has_permissions(company_id=company_id, user_id=acting_user_id,
                                                                      required_role=CompanyRole.ADMIN)

        filters = {CompanyJoinRequestModel.company_id: company_id,
                   CompanyJoinRequestModel.status: MessageStatus.PENDING}
        requests = await self.repo.get_instances_data_paginated(page=page, page_size=page_size, filters=filters)
        return requests

    async def get_pending_for_user(self, user_id: UUID, page: int = 1, page_size: int = 100) -> PaginationResponse[
        SchemaType]:
        filters = {CompanyJoinRequestModel.requesting_user_id: user_id,
                   CompanyJoinRequestModel.status: MessageStatus.PENDING}
        requests = await self.repo.get_instances_data_paginated(page=page, page_size=page_size, filters=filters)
        return requests

    async def _get_and_assert_role(self, request_id: UUID, acting_user_id: UUID) -> CompanyJoinRequestModel:
        """
        Helper method to get request and verify acting_user_id as Admin or higher role.
        :param request_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: request
        """
        request = await self.repo.get_instance_by_field_or_404(CompanyJoinRequestModel.id, value=request_id)
        await self.company_member_service.assert_user_has_permissions(company_id=request.company_id,
                                                                      user_id=acting_user_id,
                                                                      required_role=CompanyRole.ADMIN)
        return request
