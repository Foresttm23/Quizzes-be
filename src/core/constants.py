from enum import Enum

MINUTE = 60
HOUR = 3600
DAY = 86400


class CacheConfig(Enum):
    """(prefix: str, expire: int) expire is in seconds."""

    QUIZ_QUESTIONS_AND_OPTIONS = ("quiz_questions_and_options", DAY)
    QUIZ_TIME_LIMIT_MINUTES = ("quiz_time_limit_minutes", DAY)
    USER_STATS_IN_COMPANY = ("user_stats_in_company", 5 * MINUTE)
    USER_STATS_SYSTEM_WIDE = ("user_stats_system_wide", 5 * MINUTE)

    @property
    def prefix(self) -> str:
        return self.value[0]

    @property
    def expire(self) -> int:
        return self.value[1]
