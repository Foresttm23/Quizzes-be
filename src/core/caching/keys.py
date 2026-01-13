from uuid import UUID

from .config import CacheConfig
from .manager import CacheManager


def attempt_details(
        user_id: UUID, attempt_id: UUID
) -> str:  # Not really needed, since it won't be invalidated after completion.
    return CacheManager.build_key(
        CacheConfig.ATTEMPT_DETAILS.prefix, user_id=user_id, attempt_id=attempt_id
    )


def quiz_questions_and_options(company_id: UUID, quiz_id: UUID) -> str:
    return CacheManager.build_key(
        CacheConfig.QUIZ_QUESTIONS.prefix,
        company_id=company_id,
        quiz_id=quiz_id,
    )


def quiz_time_limit_minutes(company_id: UUID, quiz_id: UUID) -> str:
    return CacheManager.build_key(
        CacheConfig.QUIZ_TIME_LIMIT.prefix,
        company_id=company_id,
        quiz_id=quiz_id,
    )


def user_stats_in_company(
        company_id: UUID, acting_user_id: UUID, target_user_id: UUID
) -> str:
    return CacheManager.build_key(
        CacheConfig.USER_STATS.prefix,
        company_id=company_id,
        acting_user_id=acting_user_id,
        target_user_id=target_user_id,
    )


def user_stats_system_wide(user_id) -> str:
    return CacheManager.build_key(
        CacheConfig.USER_STATS.prefix, user_id=user_id
    )
