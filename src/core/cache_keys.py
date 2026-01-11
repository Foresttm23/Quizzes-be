from uuid import UUID

from .cache import build_cache_key
from .constants import CacheConfig


class CacheKeyFactory:
    @staticmethod
    def attempt_details(user_id: UUID, attempt_id: UUID) -> str:  # Not really needed, since it wont be invalidated after completion.
        return build_cache_key(CacheConfig.ATTEMPT_DETAILS.prefix, user_id=user_id, attempt_id=attempt_id)

    @staticmethod
    def quiz_questions_and_options(company_id: UUID, quiz_id: UUID) -> str:
        return build_cache_key(CacheConfig.QUIZ_QUESTIONS_AND_OPTIONS.prefix, company_id=company_id, quiz_id=quiz_id)

    @staticmethod
    def quiz_time_limit_minutes(company_id: UUID, quiz_id: UUID) -> str:
        return build_cache_key(CacheConfig.QUIZ_TIME_LIMIT_MINUTES.prefix, company_id=company_id, quiz_id=quiz_id)

    @staticmethod
    def user_stats_in_company(company_id: UUID, acting_user_id: UUID, target_user_id: UUID) -> str:
        return build_cache_key(
            CacheConfig.USER_STATS_IN_COMPANY.prefix, company_id=company_id, acting_user_id=acting_user_id, target_user_id=target_user_id
        )

    @staticmethod
    def user_stats_system_wide(user_id) -> str:
        return build_cache_key(CacheConfig.USER_STATS_SYSTEM_WIDE.prefix, user_id=user_id)
