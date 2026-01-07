from __future__ import annotations

from typing import Sequence, Any
from uuid import UUID, uuid4

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from core.exceptions import InstanceNotFoundException, InvalidRecipientException, PermissionDeniedException, \
    UserIsNotACompanyMemberException, CompanyPermissionException, UserAlreadyInCompanyException, \
    ResourceConflictException
from core.logger import logger
from core.schemas import PaginationResponse
from core.service import BaseService
from .enums import MessageStatus, CompanyRole
from .models import Company as CompanyModel, Invitation as CompanyInvitationModel, \
    JoinRequest as CompanyJoinRequestModel, Member as CompanyMemberModel
from .repository import CompanyRepository, InvitationRepository, MemberRepository, JoinRequestRepository
from .schemas import CompanyCreateRequestSchema, CompanyUpdateInfoRequestSchema
from .utils import CompanyUtils


class JoinRequestService(BaseService[JoinRequestRepository]):
    @property
    def display_name(self) -> str:
        return "JoinRequest"

    def __init__(self, db: AsyncSession, member_service: MemberService):
        super().__init__(repo=JoinRequestRepository(db=db))
        self.member_service = member_service
        self.company_utils = CompanyUtils()

    async def create_join_request(self, company_id: UUID, requesting_user_id: UUID) -> CompanyJoinRequestModel:
        """
        Creates request from user to a desired company.
        :param company_id:
        :param requesting_user_id: is the same as user.id from JWT token
        :return: request
        """
        await self.member_service.assert_user_not_in_company(company_id=company_id, user_id=requesting_user_id)
        await self._assert_no_join_request_exists(company_id=company_id, requesting_user_id=requesting_user_id)

        new_request = CompanyJoinRequestModel(id=uuid4(), company_id=company_id, requesting_user_id=requesting_user_id)
        logger.info(f"Created new join_request: {new_request.id} requesting_user_id {requesting_user_id}")

        await self.repo.save_and_refresh(new_request)
        return new_request

    async def _assert_no_join_request_exists(self, company_id: UUID, requesting_user_id: UUID):
        filters = {CompanyJoinRequestModel.company_id: company_id,
                   CompanyJoinRequestModel.requesting_user_id: requesting_user_id,
                   CompanyJoinRequestModel.status: MessageStatus.PENDING}
        request = await self.repo.get_instance_by_filters_or_none(filters=filters)
        if request:
            raise ResourceConflictException(message="You already have a pending request for this company.")

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
                                      page_size: int = 100, ) -> PaginationResponse[CompanyJoinRequestModel]:
        acting_user_role = await self.member_service.repo.get_company_role(company_id=company_id,
                                                                           user_id=acting_user_id)
        self.company_utils.validate_user_role(user_role=acting_user_role, required_role=CompanyRole.ADMIN)

        filters = {CompanyJoinRequestModel.company_id: company_id,
                   CompanyJoinRequestModel.status: MessageStatus.PENDING, }
        requests = await self.repo.get_instances_paginated(page=page, page_size=page_size, filters=filters)
        return requests

    async def get_pending_for_user(self, user_id: UUID, page: int = 1, page_size: int = 100) -> PaginationResponse[
        CompanyJoinRequestModel]:
        filters = {CompanyJoinRequestModel.requesting_user_id: user_id,
                   CompanyJoinRequestModel.status: MessageStatus.PENDING, }
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
        acting_user_role = await self.member_service.repo.get_company_role(company_id=request.company_id,
                                                                           user_id=acting_user_id)
        self.company_utils.validate_user_role(user_role=acting_user_role, required_role=CompanyRole.ADMIN)
        return request

    async def get_request(self, request_id: UUID,
                          relationships: set[InstrumentedAttribute] | None = None) -> CompanyJoinRequestModel:
        request = await self.repo.get_instance_by_field_or_none(CompanyJoinRequestModel.id, value=request_id,
                                                                relationships=relationships)
        if not request:
            raise InstanceNotFoundException(instance_name=self.display_name)
        return request


class MemberService(BaseService[MemberRepository]):
    @property
    def display_name(self) -> str:
        return "CompanyMember"

    def __init__(self, db: AsyncSession):
        super().__init__(repo=MemberRepository(db=db))
        self.company_utils = CompanyUtils()

    async def get_members_paginated(self, page: int, page_size: int, company_id: UUID,
                                    role: CompanyRole | None = None, ) -> PaginationResponse[CompanyMemberModel]:
        filters: dict[InstrumentedAttribute, Any] = {CompanyMemberModel.company_id: company_id}
        if role:
            filters[CompanyMemberModel.role] = role

        return await self.repo.get_instances_paginated(page=page, page_size=page_size, filters=filters)

    async def remove_member(self, company_id: UUID, acting_user_id: UUID, target_user_id: UUID) -> None:
        """
        Removes a user from a Company, only if the acting_user has a role higher than the user getting removed.
        :param company_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :param target_user_id: user that is getting removed
        :return: None
        """
        target_member = await self.get_member(company_id=company_id, user_id=target_user_id)

        acting_user_role = await self.repo.get_company_role(company_id=company_id, user_id=acting_user_id)
        self.company_utils.validate_user_role(user_role=acting_user_role, required_role=target_member.role,
                                              strictly_higher=True, )

        await self._delete_instance(target_member)
        await self.repo.commit()

    async def leave_company(self, company_id: UUID, user_id: UUID) -> None:
        """
        Leave a Company.
        :param company_id:
        :param user_id: is the user from jwt token
        :return: None
        """
        member = await self.get_member(company_id=company_id, user_id=user_id)
        if member.role == CompanyRole.OWNER:
            raise ResourceConflictException(message="Owners can't leave their companies.")

        await self._delete_instance(member)
        await self.repo.commit()

    async def get_user_company_ids(self, user_id: UUID) -> Sequence[UUID]:
        user_company_ids = await self.repo.get_user_company_ids(user_id=user_id)
        return user_company_ids

    async def assert_user_in_company(self, company_id: UUID, user_id: UUID) -> None:
        member = await self._get_member_or_none(company_id=company_id, user_id=user_id)
        if not member:
            raise UserIsNotACompanyMemberException()

    async def get_member(self, company_id: UUID, user_id: UUID,
                         relationships: set[InstrumentedAttribute] | None = None, ) -> CompanyMemberModel:
        """
        :param company_id:
        :param user_id:
        :param relationships:
        :return: Company Member
        :raise InstanceNotFoundException:
        """
        member = await self._get_member_or_none(company_id=company_id, user_id=user_id, relationships=relationships)
        if not member:
            raise InstanceNotFoundException(instance_name=self.display_name)
        return member

    async def _get_member_or_none(self, company_id: UUID, user_id: UUID, relationships: set[
                                                                                            InstrumentedAttribute] | None = None, ) -> CompanyMemberModel | None:
        """
        :param company_id:
        :param user_id:
        :param relationships:
        :return: Company Member | None
        """
        filters = {CompanyMemberModel.company_id: company_id, CompanyMemberModel.user_id: user_id, }
        return await self.repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships)



    async def assert_user_permissions(self, company_id: UUID, user_id: UUID, required_role: CompanyRole,
                                      strictly_higher: bool = False, ) -> None:
        user_role = await self.repo.get_company_role(company_id=company_id, user_id=user_id)
        self.company_utils.validate_user_role(user_role=user_role, required_role=required_role,
                                              strictly_higher=strictly_higher, )

    async def assert_user_not_in_company(self, company_id: UUID, user_id: UUID) -> None:
        member = await self._get_member_or_none(company_id=company_id, user_id=user_id)
        if member:
            raise UserAlreadyInCompanyException()

    async def has_user_permissions(self, company_id: UUID, user_id: UUID, required_role: CompanyRole,
                                   strictly_higher: bool = False, ) -> bool:
        """
        :param company_id:
        :param user_id:
        :param required_role:
        :param strictly_higher:
        :return: True If allowed, False otherwise.
        """
        try:
            await self.assert_user_permissions(company_id, user_id, required_role, strictly_higher)
            return True
        except (UserIsNotACompanyMemberException, CompanyPermissionException):
            return False

    async def update_role(self, company_id: UUID, target_user_id: UUID, acting_user_id: UUID,
                          new_role: CompanyRole, ) -> CompanyMemberModel:
        target_member = await self.get_member(company_id=company_id, user_id=target_user_id)

        # Only Owner can update the member roles for now, can be changed in the future though
        acting_member_role = await self.repo.get_company_role(company_id=company_id, user_id=acting_user_id)
        self.company_utils.validate_user_role(user_role=acting_member_role, required_role=CompanyRole.OWNER)

        acting_member_role.role = new_role

        await self.repo.save_and_refresh(target_member)
        logger.info(f"Updated role: {new_role} user {target_member.id} company {company_id} by {acting_user_id}")

        return target_member

    async def get_and_lock_member_row(self, company_id: UUID, user_id: UUID) -> CompanyMemberModel | None:
        member = await self.repo.get_and_lock_member_row(company_id=company_id, user_id=user_id)
        if member is None:
            raise UserIsNotACompanyMemberException()

        return member


class InvitationService(BaseService[InvitationRepository]):
    @property
    def display_name(self) -> str:
        return "Invitation"

    def __init__(self, db: AsyncSession, member_service: MemberService):
        super().__init__(repo=InvitationRepository(db=db))
        self.member_service = member_service
        self.company_utils = CompanyUtils()

    async def create_invitation(self, company_id: UUID, invited_user_id: UUID,
                                acting_user_id: UUID) -> CompanyInvitationModel:
        """
        Send invitation from a company to a user
        :param company_id:
        :param invited_user_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: invitation
        """
        acting_user_role = await self.member_service.repo.get_company_role(company_id=company_id,
                                                                           user_id=acting_user_id)
        self.company_utils.validate_user_role(user_role=acting_user_role, required_role=CompanyRole.ADMIN)

        await self.member_service.assert_user_not_in_company(company_id=company_id, user_id=invited_user_id)
        await self._assert_no_invitation_exists(company_id=company_id, invited_user_id=invited_user_id)

        new_invitation = CompanyInvitationModel(id=uuid4(), company_id=company_id, invited_user_id=invited_user_id,
                                                status=MessageStatus.PENDING)

        await self.repo.save_and_refresh(new_invitation)
        logger.info(
            f"Created new invitation: {new_invitation.id} invited_user {invited_user_id} by: company {company_id} member {acting_user_id}")

        return new_invitation

    async def _assert_no_invitation_exists(self, company_id: UUID, invited_user_id: UUID):
        filters = {CompanyInvitationModel.company_id: company_id,
                   CompanyInvitationModel.invited_user_id: invited_user_id,
                   CompanyInvitationModel.status: MessageStatus.PENDING}
        invitation = await self.repo.get_instance_by_filters_or_none(filters=filters)
        if invitation:
            raise ResourceConflictException(message="You already have a pending request for this company.")

    async def accept_from_company(self, invitation_id: UUID, invited_user_id: UUID) -> tuple[
        CompanyInvitationModel, CompanyMemberModel]:
        """
        Accept invitation from a company by a user.
        :param invitation_id:
        :param invited_user_id: the user from jwt dependency
        :return: invitation
        """
        invitation = await self._get_and_verify_invited_user_id(invitation_id=invitation_id,
                                                                invited_user_id=invited_user_id)

        invitation.status = MessageStatus.ACCEPTED

        new_member = CompanyMemberModel(company_id=invitation.company_id, user_id=invitation.invited_user_id)
        await self.repo.save_and_refresh(invitation, new_member)
        logger.info(f"Accepted invitation: {invitation.id} company {invitation.company_id} by {invited_user_id}")

        return invitation, new_member

    async def decline_from_company(self, invitation_id: UUID, invited_user_id: UUID) -> CompanyInvitationModel:
        """
        Deline invitation from a company by a user.
        :param invitation_id:
        :param invited_user_id:
        :return: invitation
        """
        invitation = await self._get_and_verify_invited_user_id(invitation_id=invitation_id,
                                                                invited_user_id=invited_user_id)

        invitation.status = MessageStatus.DECLINED

        await self.repo.save_and_refresh(invitation)
        logger.info(
            f"Declined company invitation: {invitation.id} company {invitation.company_id} by {invitation.invited_user_id}")

        return invitation

    async def cancel_by_company(self, invitation_id: UUID, acting_user_id: UUID) -> CompanyInvitationModel:
        """
        Cancel an invitation to a user by a company.
        :param invitation_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: invitation
        """
        invitation = await self.get_invitation(invitation_id=invitation_id)
        acting_user_role = await self.member_service.repo.get_company_role(company_id=invitation.company_id,
                                                                           user_id=acting_user_id)
        self.company_utils.validate_user_role(user_role=acting_user_role, required_role=CompanyRole.ADMIN)

        invitation.status = MessageStatus.CANCELED

        await self.repo.save_and_refresh(invitation)
        logger.info(
            f"Cancel invitation: {invitation.id} user {invitation.invited_user_id} by: company {invitation.company_id} member {acting_user_id}")

        return invitation

    async def get_pending_for_user(self, user_id: UUID, page: int, page_size: int) -> PaginationResponse[
        CompanyInvitationModel]:
        filters = {CompanyInvitationModel.invited_user_id: user_id,
                   CompanyInvitationModel.status: MessageStatus.PENDING, }
        invitations = await self.repo.get_instances_paginated(page=page, page_size=page_size, filters=filters)
        return invitations

    async def get_pending_for_company(self, company_id: UUID, acting_user_id: UUID, page: int, page_size: int) -> \
            PaginationResponse[CompanyInvitationModel]:
        acting_user_role = await self.member_service.repo.get_company_role(company_id=company_id,
                                                                           user_id=acting_user_id)
        self.company_utils.validate_user_role(user_role=acting_user_role, required_role=CompanyRole.ADMIN)

        filters = {CompanyInvitationModel.company_id: company_id,
                   CompanyInvitationModel.status: MessageStatus.PENDING, }
        invitations = await self.repo.get_instances_paginated(page=page, page_size=page_size, filters=filters)
        return invitations

    async def _get_and_verify_invited_user_id(self, invitation_id: UUID,
                                              invited_user_id: UUID) -> CompanyInvitationModel:
        """
        Helper method to get invitation and verify invited_user_id == invitation.invited_user_id.
        :param invitation_id:
        :param invited_user_id:
        :return: invitation
        """
        invitation = await self.get_invitation(invitation_id=invitation_id)
        if invitation.invited_user_id != invited_user_id:
            raise InvalidRecipientException()

        return invitation

    async def get_invitation(self, invitation_id: UUID) -> CompanyInvitationModel:
        invitation = await self.repo.get_instance_by_field_or_none(CompanyInvitationModel.id, value=invitation_id)
        if not invitation:
            raise InstanceNotFoundException(instance_name=self.display_name)
        return invitation


class CompanyService(BaseService[CompanyRepository]):
    @property
    def display_name(self) -> str:
        return "Company"

    def __init__(self, db: AsyncSession, member_service: MemberService):
        super().__init__(repo=CompanyRepository(db=db))
        self.member_service = member_service
        self.company_utils = CompanyUtils()

    async def get_companies_paginated(self, user_id: UUID | None, page: int, page_size: int) -> PaginationResponse[
        CompanyModel]:
        if not user_id:
            return await self._get_visible_companies_paginated(page=page, page_size=page_size)

        user_company_ids = await self.member_service.get_user_company_ids(user_id=user_id)

        if not user_company_ids:
            return await self._get_visible_companies_paginated(page=page, page_size=page_size)

        return await self._get_visible_and_user_companies_paginated(page=page, page_size=page_size,
                                                                    user_company_ids=user_company_ids)

    async def _get_visible_companies_paginated(self, page: int, page_size: int):
        filters = {CompanyModel.is_visible: True}
        return await self.repo.get_instances_paginated(page=page, page_size=page_size, filters=filters)

    async def _get_visible_and_user_companies_paginated(self, page: int, page_size: int,
                                                        user_company_ids: Sequence[UUID]):
        condition = or_(CompanyModel.is_visible.is_(True), CompanyModel.id.in_(user_company_ids))

        query = select(CompanyModel).where(condition)
        query = query.order_by(CompanyModel.id.desc())

        return await self.repo.paginate_query(query, page, page_size)

    async def get_by_id(self, company_id: UUID, user_id: UUID | None) -> CompanyModel:
        company = await self.get_company(company_id=company_id)
        if company.is_visible:
            return company

        # Invisible company then check if user is a part of it
        if not user_id:
            raise InstanceNotFoundException()

        await self.member_service.assert_user_in_company(company_id=company_id, user_id=user_id)
        return company

    async def create_company(self, acting_user_id: UUID, company_info: CompanyCreateRequestSchema) -> CompanyModel:
        """Creates a new Company"""
        company_data = company_info.model_dump()
        company = CompanyModel(id=uuid4(), **company_data)
        owner = CompanyMemberModel(company_id=company.id, user_id=acting_user_id, role=CompanyRole.OWNER)

        await self.repo.save_and_refresh(company, owner)
        logger.info(f"Created new company: {company.id} by {owner.user_id}")

        return company

    async def update_company(self, company_id: UUID, acting_user_id: UUID,
                             company_info: CompanyUpdateInfoRequestSchema, ) -> CompanyModel:
        company = await self.get_company(company_id=company_id)
        acting_user_role = await self.member_service.repo.get_company_role(company_id=company.id,
                                                                           user_id=acting_user_id)
        self.company_utils.validate_user_role(user_role=acting_user_role, required_role=CompanyRole.ADMIN)

        company = self._update_instance(instance=company, new_data=company_info, by=acting_user_id)
        await self.repo.save_and_refresh(company)
        logger.info(f"Updated {self.display_name}: {company.id} by {acting_user_id}")

        return company

    async def delete_company(self, company_id: UUID, acting_user_id: UUID):
        company = await self.get_company(company_id=company_id)
        acting_user_role = await self.member_service.repo.get_company_role(company_id=company.id,
                                                                           user_id=acting_user_id)
        self.company_utils.validate_user_role(user_role=acting_user_role, required_role=CompanyRole.OWNER)

        await self._delete_instance(instance=company)
        await self.repo.commit()

    async def get_company(self, company_id: UUID,
                          relationships: set[InstrumentedAttribute] | None = None) -> CompanyModel:
        company = await self.repo.get_instance_by_field_or_none(CompanyModel.id, value=company_id,
                                                                relationships=relationships)
        if not company:
            raise InstanceNotFoundException(instance_name=self.display_name)
        return company
