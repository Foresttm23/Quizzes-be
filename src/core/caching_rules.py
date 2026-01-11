from typing import Any

from src.quiz.enums import AttemptStatus


def cache_attempt_if_finished(attempt: Any) -> bool:
    """Returns True if finished."""
    status = getattr(attempt, "status", None)
    return status is not None and status != AttemptStatus.IN_PROGRESS
