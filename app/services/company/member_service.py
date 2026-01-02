from typing import Sequence, Any
from uuid import UUID

from pygments.lexers import q
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.exceptions import InstanceNotFoundException
from app.core.exceptions import UserIsNotACompanyMemberException, CompanyPermissionException, \
    UserAlreadyInCompanyException, ResourceConflictException
from app.core.logger import logger
from app.db.models import Member as CompanyMemberModel
from app.db.repository.company.member_repository import CompanyMemberRepository
from app.services.base_service import BaseService
from app.utils.enum_utils import CompanyRole
from schemas.base_schemas import PaginationResponse


class CompanyMemberService(BaseService[CompanyMemberRepository]):
    @property
    def display_name(self) -> str:
        return "CompanyMember"

    def __init__(self, db: AsyncSession):
        super().__init__(repo=CompanyMemberRepository(db=db))

    async def get_members_paginated(self, page: int, page_size: int, company_id: UUID,
                                    role: CompanyRole | None = None) -> PaginationResponse[CompanyMemberModel]:
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
        self.validate_user_role(user_role=acting_user_role, required_role=target_member.role, strictly_higher=True)

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
                         relationships: set[InstrumentedAttribute] | None = None) -> CompanyMemberModel:
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

    async def _get_member_or_none(self, company_id: UUID, user_id: UUID,
                                  relationships: set[InstrumentedAttribute] | None = None) -> CompanyMemberModel | None:
        """
        :param company_id:
        :param user_id:
        :param relationships:
        :return: Company Member | None
        """
        filters = {CompanyMemberModel.company_id: company_id, CompanyMemberModel.user_id: user_id}
        return await self.repo.get_instance_by_filters_or_none(filters=filters, relationships=relationships)

    @staticmethod
    def validate_user_role(user_role: CompanyRole, required_role: CompanyRole, strictly_higher: bool = False) -> None:
        if user_role is None:
            raise UserIsNotACompanyMemberException()

        if strictly_higher:
            if user_role <= required_role:
                raise CompanyPermissionException()
        else:
            if user_role < required_role:
                raise CompanyPermissionException()

    async def assert_user_permissions(self, company_id: UUID, user_id: UUID, required_role: CompanyRole,
                                      strictly_higher: bool = False) -> None:
        user_role = await self.repo.get_company_role(company_id=company_id, user_id=user_id)
        self.validate_user_role(user_role=user_role, required_role=required_role, strictly_higher=strictly_higher)

    async def assert_user_not_in_company(self, company_id: UUID, user_id: UUID) -> None:
        member = await self._get_member_or_none(company_id=company_id, user_id=user_id)
        if member:
            raise UserAlreadyInCompanyException()

    async def has_user_permissions(self, company_id: UUID, user_id: UUID, required_role: CompanyRole,
                                   strictly_higher: bool = False) -> bool:
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
                          new_role: CompanyRole) -> CompanyMemberModel:
        target_member = await self.get_member(company_id=company_id, user_id=target_user_id)

        # Only Owner can update the member roles for now, can be changed in the future though
        acting_member_role = await self.repo.get_company_role(company_id=company_id, user_id=acting_user_id)
        self.validate_user_role(user_role=acting_member_role, required_role=CompanyRole.OWNER)

        acting_member_role.role = new_role

        await self.repo.save_and_refresh(target_member)
        logger.info(f"Updated role: {new_role} user {target_member.id} company {company_id} by {acting_user_id}")

        return target_member
