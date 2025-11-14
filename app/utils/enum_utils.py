from enum import IntEnum


class CompanyRole(IntEnum):
    OWNER = 1000
    ADMIN = 500
    MEMBER = 100
    GUEST = 0
