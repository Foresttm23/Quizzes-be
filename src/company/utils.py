from __future__ import annotations

from core.exceptions import UserIsNotACompanyMemberException, CompanyPermissionException
from .enums import CompanyRole


class CompanyUtils:
    def __init__(self):
        pass

    @staticmethod
    def validate_user_role(user_role: CompanyRole, required_role: CompanyRole, strictly_higher: bool = False, ) -> None:
        if user_role is None:
            raise UserIsNotACompanyMemberException()

        if strictly_higher:
            if user_role <= required_role:
                raise CompanyPermissionException()
        else:
            if user_role < required_role:
                raise CompanyPermissionException()
