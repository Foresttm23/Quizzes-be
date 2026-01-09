from typing import Annotated

from fastapi import Depends

from core.dependencies import DBSessionDep
from src.company.dependencies import CompanyMemberServiceDep

from .service import AttemptService, QuizService


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
