from enum import Enum

MINUTE = 60
HOUR = 3600
DAY = 86400


class CacheConfig(Enum):  # TODO Pydantic settings.
    """(prefix: str, expire: int) expire is in seconds."""
    QUIZ_TIME_LIMIT = ("quiz:time_limit", DAY)
    QUIZ_QUESTIONS = ("quiz:questions", 2 * DAY)
    ATTEMPT_DETAILS = ("attempt:details", 2 * DAY)
    # Correct as long as company and sys stats have different args
    USER_STATS = ("user:stats", 5 * MINUTE)

    @property
    def prefix(self) -> str:
        return self.value[0]

    @property
    def expire(self) -> int:
        return self.value[1]
