from typing import Sequence
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidRecipientException
from app.db.models.company_invitations_model import CompanyInvitation as CompanyInvitationModel
from app.db.models.company_member_model import CompanyMember as CompanyMemberModel
from app.db.repository.company_invitation_repository import CompanyInvitationRepository
from app.schemas.company_inv_req_schemas.company_inv_req_schema import UpdateInvitationSchema
from app.services.base_service import BaseService
from app.services.company_member_service import CompanyMemberService
from app.utils.enum_utils import CompanyRole, MessageStatus


class CompanyInvitationService(BaseService[CompanyInvitationRepository]):
    @property
    def display_name(self) -> str:
        return "Invitation"

    def __init__(self, db: AsyncSession, company_member_service: CompanyMemberService):
        super().__init__(repo=CompanyInvitationRepository(db=db))
        self.company_member_service = company_member_service

    async def send_invitation_to_user(self, company_id: UUID, invited_user_id: UUID,
                                      acting_user_id: UUID) -> CompanyInvitationModel:
        """
        Send invitation from a company to a user
        :param company_id:
        :param invited_user_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: invitation
        """
        await self.company_member_service.assert_user_has_role(company_id=company_id, user_id=acting_user_id,
                                                               required_role=CompanyRole.ADMIN)
        new_invitation = CompanyInvitationModel(id=uuid4(), company_id=company_id, invited_user_id=invited_user_id,
                                                status=MessageStatus.PENDING)

        await self.repo.save_changes_and_refresh(new_invitation)
        return new_invitation

    async def accept_invitation_from_company(self, invitation_id: UUID, invited_user_id: UUID) -> tuple[
        CompanyInvitationModel, CompanyMemberModel]:
        """
        Accept invitation from a company by a user.
        :param invitation_id:
        :param invited_user_id: the user from jwt dependency
        :return: invitation
        """
        invitation = await self._get_invitation_and_verify_invited_user_id(invitation_id=invitation_id,
                                                                           invited_user_id=invited_user_id)

        invitation = await self._update_status(invitation=invitation, new_status=MessageStatus.ACCEPTED)

        new_member = CompanyMemberModel(company_id=invitation.company_id, user_id=invitation.invited_user_id)
        await self.repo.save_changes_and_refresh(invitation, new_member)

        return invitation, new_member

    async def decline_invitation_from_company(self, invitation_id: UUID,
                                              invited_user_id: UUID) -> CompanyInvitationModel:
        """
        Deline invitation from a company by a user.
        :param invitation_id:
        :param invited_user_id:
        :return: invitation
        """
        invitation = await self._get_invitation_and_verify_invited_user_id(invitation_id=invitation_id,
                                                                           invited_user_id=invited_user_id)

        invitation = await self._update_status(invitation=invitation, new_status=MessageStatus.DECLINED)
        await self.repo.save_changes_and_refresh(invitation)
        return invitation

    async def cancel_invitation_by_company(self, invitation_id: UUID, acting_user_id: UUID) -> CompanyInvitationModel:
        """
        Cancel an invitation to a user by a company.
        :param invitation_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :return: invitation
        """
        invitation = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=invitation_id)
        await self.company_member_service.assert_user_has_role(company_id=invitation.company_id, user_id=acting_user_id,
                                                               required_role=CompanyRole.ADMIN)

        invitation = await self._update_status(invitation=invitation, new_status=MessageStatus.CANCELED)
        await self.repo.save_changes_and_refresh(invitation)
        return invitation

    async def get_pending_invitations_for_user(self, user_id: UUID) -> Sequence[CompanyInvitationModel]:
        invitations = await self.repo.get_pending_invitations_for_user(user_id=user_id)
        return invitations

    async def get_pending_invitations_for_company(self, company_id: UUID, acting_user_id: UUID) -> Sequence[
        CompanyInvitationModel]:
        await self.company_member_service.assert_user_has_role(company_id=company_id, user_id=acting_user_id,
                                                               required_role=CompanyRole.ADMIN)
        invitations = await self.repo.get_pending_invitations_for_company(company_id=company_id)
        return invitations

    async def _update_status(self, invitation: CompanyInvitationModel,
                             new_status: MessageStatus) -> CompanyInvitationModel:
        new_invitation_data = UpdateInvitationSchema(invitation_status=new_status)
        invitation = await self._update_instance(instance=invitation, new_data=new_invitation_data)
        return invitation

    async def _get_invitation_and_verify_invited_user_id(self, invitation_id: UUID,
                                                         invited_user_id: UUID) -> CompanyInvitationModel:
        """
        Helper method to get invitation and verify invited_user_id == invitation.invited_user_id.
        :param invitation_id:
        :param invited_user_id:
        :return: invitation
        """
        invitation = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=invitation_id)
        if invitation.invited_user_id != invited_user_id:
            raise InvalidRecipientException()

        return invitation
