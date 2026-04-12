import asyncio
from uuid import UUID

from sqlalchemy import event
from sqlalchemy.orm import Session

from quiz.models import CompanyQuiz, QuizAttempt
from .config import CacheConfig
from .operations import invalidate_mapping


def add_to_session(session: Session, key: str, _ids: set[UUID]):
    if _ids:
        if key not in session.info:
            session.info[key] = set()
        session.info[key].update(_ids)


@event.listens_for(Session, "after_flush")
def capture_ids_for_invalidation(session, flush_context):
    changed_objects = session.dirty | session.new | session.deleted

    quiz_ids = set()
    attempt_ids = set()

    for obj in changed_objects:
        if isinstance(obj, CompanyQuiz):
            quiz_ids.add(obj.id)
        elif isinstance(obj, QuizAttempt):
            attempt_ids.add(obj.id)

    add_to_session(session, "quiz_ids_to_invalidate", quiz_ids)
    add_to_session(session, "attempt_ids_to_invalidate", attempt_ids)


@event.listens_for(Session, "after_commit")
def trigger_invalidation_after_commit(session):
    quiz_ids = session.info.pop("quiz_ids_to_invalidate", set())
    attempt_ids = session.info.pop("attempt_ids_to_invalidate", set())

    loop = asyncio.get_event_loop()
    if not loop.is_running():
        return

    for _id in quiz_ids:
        loop.create_task(invalidate_mapping(CacheConfig.QUIZ.get_mapping_key(_id)))

    for _id in attempt_ids:
        loop.create_task(invalidate_mapping(CacheConfig.ATTEMPT.get_mapping_key(_id)))
