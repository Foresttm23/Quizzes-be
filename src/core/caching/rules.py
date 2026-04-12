from quiz.enums import AttemptStatus
from quiz.schemas import QuizAttemptBaseSchema


# Might use a specific schema, but since I might call it for other attempts schema, left as is
def cache_attempt_if_finished(attempt: QuizAttemptBaseSchema) -> bool:
    """Returns True if finished."""
    return attempt.status != AttemptStatus.IN_PROGRESS
