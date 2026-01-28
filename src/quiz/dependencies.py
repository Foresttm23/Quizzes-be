from typing import Annotated

from fastapi import Depends
from fastapi_limiter.depends import RateLimiter

from src.company.dependencies import CompanyMemberServiceDep
from src.core.dependencies import DBSessionDep

from .service import AttemptService, QuizService

QuizLimitDep = Depends(RateLimiter(times=20, seconds=60))
AttemptLimitDep = Depends(RateLimiter(times=20, seconds=60))


async def get_company_quiz_service(
    db: DBSessionDep, member_service: CompanyMemberServiceDep
) -> QuizService:
    return QuizService(db=db, member_service=member_service)


CompanyQuizServiceDep = Annotated[QuizService, Depends(get_company_quiz_service)]


async def get_attempt_service(
    db: DBSessionDep,
    member_service: CompanyMemberServiceDep,
    quiz_service: CompanyQuizServiceDep,
) -> AttemptService:
    return AttemptService(
        db=db, member_service=member_service, quiz_service=quiz_service
    )


AttemptServiceDep = Annotated[AttemptService, Depends(get_attempt_service)]
