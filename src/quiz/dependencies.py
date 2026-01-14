from typing import Annotated

from fastapi import Depends

from src.company.dependencies import CompanyMemberServiceDep
from src.core.dependencies import DBSessionDep, CacheManagerDep
from .service import AttemptService, QuizService


async def get_company_quiz_service(
        db: DBSessionDep, cache_manager: CacheManagerDep, member_service: CompanyMemberServiceDep
) -> QuizService:
    return QuizService(db=db, cache_manager=cache_manager, member_service=member_service)


CompanyQuizServiceDep = Annotated[QuizService, Depends(get_company_quiz_service)]


async def get_attempt_service(
        db: DBSessionDep,
        cache_manager: CacheManagerDep,
        member_service: CompanyMemberServiceDep,
        quiz_service: CompanyQuizServiceDep,
) -> AttemptService:
    return AttemptService(
        db=db, cache_manager=cache_manager, member_service=member_service, quiz_service=quiz_service
    )


AttemptServiceDep = Annotated[AttemptService, Depends(get_attempt_service)]
