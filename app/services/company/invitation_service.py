from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InstanceNotFoundException
from app.core.exceptions import InvalidRecipientException
from app.core.logger import logger
from app.db.models.company.invitation_model import Invitation as CompanyInvitationModel
from app.db.models.company.member_model import Member as CompanyMemberModel
from app.db.repository.company.invitation_repository import CompanyInvitationRepository
from app.schemas.base_schemas import PaginationResponse
from app.services.base_service import BaseService
from app.services.company.member_service import CompanyMemberService
from app.utils.enum_utils import CompanyRole, MessageStatus


class CompanyInvitationService(BaseService[CompanyInvitationRepository]):
    @property
    def display_name(self) -> str:
        return "Invitation"

    def __init__(self, db: AsyncSession, company_member_service: CompanyMemberService):
        super().__init__(repo=CompanyInvitationRepository(db=db))
        self.company_member_service = company_member_service

    async def create_invitation(self, company_id: UUID, invited_user_id: UUID,
                                acting_user_id: UUID) -> CompanyInvitationModel:
        """
        Send invitation from a company to a user
        :param company_id:
        :param invited_user_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: invitation
        """
        acting_user_role = await self.company_member_service.repo.get_company_role(company_id=company_id,
                                                                                   user_id=acting_user_id)
        self.company_member_service.validate_user_role(user_role=acting_user_role, required_role=CompanyRole.ADMIN)

        await self.company_member_service.assert_user_not_in_company(company_id=company_id, user_id=invited_user_id)

        new_invitation = CompanyInvitationModel(id=uuid4(), company_id=company_id, invited_user_id=invited_user_id,
                                                status=MessageStatus.PENDING, )

        await self.repo.save_and_refresh(new_invitation)
        logger.info(
            f"Created new invitation: {new_invitation.id} invited_user {invited_user_id} by: company {company_id} member {acting_user_id}")

        return new_invitation

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
        acting_user_role = await self.company_member_service.repo.get_company_role(company_id=invitation.company_id,
                                                                                   user_id=acting_user_id)
        self.company_member_service.validate_user_role(user_role=acting_user_role, required_role=CompanyRole.ADMIN)

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
        acting_user_role = await self.company_member_service.repo.get_company_role(company_id=company_id,
                                                                                   user_id=acting_user_id)
        self.company_member_service.validate_user_role(user_role=acting_user_role, required_role=CompanyRole.ADMIN)

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
