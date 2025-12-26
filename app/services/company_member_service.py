from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserIsNotACompanyMemberException, CompanyPermissionException, \
    UserAlreadyInCompanyException
from app.core.logger import logger
from app.db.models.company_member_model import CompanyMember as CompanyMemberModel
from app.db.repository.company_member_repository import CompanyMemberRepository
from app.services.base_service import BaseService
from app.utils.enum_utils import CompanyRole
from schemas.company_members_schemas.company_member_response_schema import UpdateMemberRoleSchema


class CompanyMemberService(BaseService[CompanyMemberRepository]):
    @property
    def display_name(self) -> str:
        return "CompanyMember"

    def __init__(self, db: AsyncSession):
        super().__init__(repo=CompanyMemberRepository(db=db))

    async def fetch_data_paginated(self, page: int, page_size: int, company_id: UUID):
        filters = {CompanyMemberModel.company_id: company_id}
        return await self.repo.get_instances_data_paginated(page=page, page_size=page_size, filters=filters)

    async def fetch_data_by_role_paginated(self, page: int, page_size: int, company_id: UUID, role: CompanyRole):
        filters = {CompanyMemberModel.company_id: company_id, CompanyMemberModel.role: role}
        return await self.repo.get_instances_data_paginated(page=page, page_size=page_size, filters=filters)

    async def remove_user_from_company(self, company_id: UUID, acting_user_id: UUID, user_id: UUID) -> None:
        """
        Removes a user from a Company, only if the acting_user has a role higher than the user getting removed.
        :param company_id:
        :param acting_user_id: id of a user with admin or higher role in a company
        :param user_id: user that is getting removed
        :return: None
        """
        await self.assert_user_in_company(company_id=company_id, user_id=user_id)
        user_role = await self.repo.get_company_role(company_id=company_id, user_id=user_id)
        await self.assert_user_has_role(company_id=company_id, user_id=acting_user_id, required_role=user_role)

        logger.debug(f"{self.display_name} remove; user_id: {user_id}, user_role: {user_role}")
        await self.repo.remove_member(company_id=company_id, user_id=user_id)
        await self.repo.save_changes_and_refresh()

    async def leave_company(self, company_id: UUID, user_id: UUID) -> None:
        """
        Leave a Company.
        :param company_id:
        :param user_id: is the user from jwt token
        :return: None
        """
        await self.assert_user_in_company(company_id=company_id, user_id=user_id)
        user_role = await self.repo.get_company_role(company_id=company_id, user_id=user_id)
        if user_role == CompanyRole.OWNER:
            # Cant leave for now, since only one Owner can be in a Company
            return

        logger.debug(f"{self.display_name} leave; user_id: {user_id}, user_role: {user_role}")
        await self.repo.remove_member(company_id=company_id, user_id=user_id)
        await self.repo.save_changes_and_refresh()

    # TODO create a method for owner to allow him to delete his companies.

    async def fetch_user_company_ids(self, user_id: UUID) -> Sequence[UUID]:
        user_company_ids = await self.repo.get_user_company_ids(user_id=user_id)
        return user_company_ids

    async def assert_user_in_company(self, company_id: UUID, user_id: UUID) -> None:
        company_member = await self.repo.get_member(company_id=company_id, user_id=user_id)
        if not company_member:
            raise UserIsNotACompanyMemberException()

    async def assert_user_has_role(self, company_id: UUID, user_id: UUID, required_role: CompanyRole,
                                   role: CompanyRole | None = None) -> None:
        if not role:
            role = await self.repo.get_company_role(company_id=company_id, user_id=user_id)
        if role is None:
            raise UserIsNotACompanyMemberException()

        if role < required_role:
            raise CompanyPermissionException()

    async def assert_user_not_in_company(self, company_id: UUID, user_id: UUID) -> None:
        company_member = await self.repo.get_member(company_id=company_id, user_id=user_id)
        if company_member:
            raise UserAlreadyInCompanyException()

    async def update_role(self, company_id: UUID, target_user_id: UUID, acting_user_id: UUID,
                          new_role: CompanyRole) -> None:
        # Only Owner can update the member roles for now, can be changed in the future though
        await self.assert_user_has_role(company_id=company_id, user_id=acting_user_id, required_role=CompanyRole.OWNER)
        target_member = await self.repo.get_member(company_id=company_id, user_id=target_user_id)

        new_role_data = UpdateMemberRoleSchema(role=new_role)
        target_member = await self._update_instance(instance=target_member, new_data=new_role_data)

        # await self.repo.update_role(new_role=new_role, company_id=company_id, user_id=target_user_id)
        await self.repo.save_changes_and_refresh(target_member)
        return target_member
