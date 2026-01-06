from enum import IntEnum, Enum


class CompanyRole(IntEnum):
    OWNER = 1000
    ADMIN = 500
    MEMBER = 100
    GUEST = 0


class MessageStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELED = "canceled"


class AttemptStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
