from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.exceptions import PermissionDeniedException
from app.core.logger import logger
from app.db.models.company.join_request_model import JoinRequest as CompanyJoinRequestModel
from app.db.models.company.member_model import Member as CompanyMemberModel
from app.schemas.base_schemas import PaginationResponse
from app.services.base_service import BaseService
from app.utils.enum_utils import MessageStatus, CompanyRole
from core.exceptions import InstanceNotFoundException
from db.repository.company.join_request_repository import CompanyJoinRequestRepository
from services.company.member_service import CompanyMemberService


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
        logger.info(f"Created new join_request: {new_request.id} requesting_user_id {requesting_user_id}")

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
        request.status = MessageStatus.ACCEPTED

        new_member = CompanyMemberModel(company_id=request.company_id, user_id=request.requesting_user_id)

        await self.repo.save_and_refresh(request, new_member)
        logger.info(
            f"Accepted request: {request.id} company {request.company_id} requesting_user {request.requesting_user_id} by {acting_user_id}")

        return request, new_member

    async def decline_request(self, request_id: UUID, acting_user_id: UUID) -> CompanyJoinRequestModel:
        """
        Decline request from user by a company.
        :param request_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: request
        """
        request = await self._get_and_assert_role(request_id=request_id, acting_user_id=acting_user_id)
        request.status = MessageStatus.DECLINED

        await self.repo.save_and_refresh(request)
        logger.info(
            f"Declined request: {request.id} company {request.company_id} requesting_user {request.requesting_user_id} by {acting_user_id}")

        return request

    async def cancel_request(self, request_id: UUID, requesting_user_id: UUID) -> CompanyJoinRequestModel:
        """
        Cancels request to company by a user.
        :param request_id:
        :param requesting_user_id: id of a user with admin or higher role in a company
        :return: request
        """
        request = await self.get_request(request_id=request_id)
        if request.requesting_user_id != requesting_user_id:
            raise PermissionDeniedException(message="Can't cancel other people requests.")

        request.status = MessageStatus.CANCELED

        await self.repo.save_and_refresh(request)
        logger.info(
            f"Canceled request: {request.id} company {request.company_id} by requesting_user {request.requesting_user_id}")

        return request

    async def get_pending_for_company(self, company_id: UUID, acting_user_id: UUID, page: int = 1,
                                      page_size: int = 100) -> PaginationResponse[CompanyJoinRequestModel]:
        acting_user_role = await self.company_member_service.repo.get_company_role(company_id=company_id,
                                                                                   user_id=acting_user_id)
        self.company_member_service.validate_user_role(user_role=acting_user_role, required_role=CompanyRole.ADMIN)

        filters = {CompanyJoinRequestModel.company_id: company_id,
                   CompanyJoinRequestModel.status: MessageStatus.PENDING}
        requests = await self.repo.get_instances_paginated(page=page, page_size=page_size, filters=filters)
        return requests

    async def get_pending_for_user(self, user_id: UUID, page: int = 1, page_size: int = 100) -> PaginationResponse[
        CompanyJoinRequestModel]:
        filters = {CompanyJoinRequestModel.requesting_user_id: user_id,
                   CompanyJoinRequestModel.status: MessageStatus.PENDING}
        requests = await self.repo.get_instances_paginated(page=page, page_size=page_size, filters=filters)
        return requests

    async def _get_and_assert_role(self, request_id: UUID, acting_user_id: UUID) -> CompanyJoinRequestModel:
        """
        Helper method to get request and verify acting_user_id as Admin or higher role.
        :param request_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: request
        """
        request = await self.get_request(request_id=request_id)
        acting_user_role = await self.company_member_service.repo.get_company_role(company_id=request.company_id,
                                                                                   user_id=acting_user_id)
        self.company_member_service.validate_user_role(user_role=acting_user_role, required_role=CompanyRole.ADMIN)
        return request

    async def get_request(self, request_id: UUID,
                          relationships: set[InstrumentedAttribute] | None = None) -> CompanyJoinRequestModel:
        request = await self.repo.get_instance_by_field_or_none(CompanyJoinRequestModel.id, value=request_id,
                                                                relationships=relationships)
        if not request:
            raise InstanceNotFoundException(instance_name=self.display_name)
        return request
