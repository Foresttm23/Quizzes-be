from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from src.company.dependencies import CompanyMemberServiceDep
from src.core.dependencies import DBSessionDep
from .service import AttemptService, QuizService


async def get_company_quiz_service(
        db: DBSessionDep, redis: Redis, member_service: CompanyMemberServiceDep
) -> QuizService:
    return QuizService(db=db, redis=redis, member_service=member_service)


CompanyQuizServiceDep = Annotated[QuizService, Depends(get_company_quiz_service)]


async def get_attempt_service(
    db: DBSessionDep,
        redis: Redis,
    member_service: CompanyMemberServiceDep,
    quiz_service: CompanyQuizServiceDep,
) -> AttemptService:
    return AttemptService(
        db=db, redis=redis, member_service=member_service, quiz_service=quiz_service
    )


AttemptServiceDep = Annotated[AttemptService, Depends(get_attempt_service)]
