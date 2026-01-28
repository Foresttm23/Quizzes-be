from __future__ import annotations

from src.core.exceptions import (
    CompanyPermissionException,
    UserIsNotACompanyMemberException,
)
from .enums import CompanyRole


def assert_user_role(
    user_role: CompanyRole | None,
    required_role: CompanyRole,
    strictly_higher: bool = False,
) -> None:
    if user_role is None:
        raise UserIsNotACompanyMemberException()

    if not user_role.is_authorized(required_role, strictly_higher):
        raise CompanyPermissionException()
