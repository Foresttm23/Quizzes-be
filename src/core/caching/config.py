from enum import Enum
from uuid import UUID

MINUTE = 60
HOUR = 3600
DAY = 86400


class CacheConfig(Enum):  # TODO Pydantic settings.
    """(prefix: str, expire: int) expire is in seconds."""
    QUIZ = ("quiz", "quiz_id", DAY)
    ATTEMPT = ("attempt", "attempt_id", 2 * DAY)
    # Correct as long as company and sys stats have different args
    USER_COMPANY_STATS = ("user:stats:company", "company_id", 5 * MINUTE)
    USER_SYSTEM_STATS = ("user:stats", "user_id", 5 * MINUTE)

    @property
    def prefix(self): return self.value[0]

    @property
    def mapping_key_name(self) -> str:
        return self.value[1]

    @property
    def expire(self) -> int:
        return self.value[2]

    def get_mapping_key(self, _id: str | UUID) -> str:
        return f"mapping:{self.prefix}:{str(_id)}"
