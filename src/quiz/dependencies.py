from typing import Annotated

from fastapi import Depends

from core.dependencies import DBSessionDep
from src.company.dependencies import CompanyMemberServiceDep
from .service import QuizService


async def get_company_quiz_service(db: DBSessionDep, member_service: CompanyMemberServiceDep) -> QuizService:
    return QuizService(db=db, member_service=member_service)


CompanyQuizServiceDep = Annotated[QuizService, Depends(get_company_quiz_service)]
