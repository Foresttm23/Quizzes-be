from enum import IntEnum, Enum


class CompanyRole(IntEnum):
    OWNER = 1000
    ADMIN = 500
    MEMBER = 100
    GUEST = 0

    def is_authorized(self, required_role: "CompanyRole", strictly_higher: bool = False) -> bool:
        if strictly_higher:
            return self.value > required_role.value
        return self.value >= required_role.value


class MessageStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELED = "canceled"
