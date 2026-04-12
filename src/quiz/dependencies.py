from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi_limiter.depends import RateLimiter

from auth.dependencies import UserRepositoryDep
from company.dependencies import CompanyMemberServiceDep
from core.dependencies import DBSessionDep
from .repository import (
    AnswerRepository,
    AttemptRepository,
    QuestionRepository,
    QuizRepository,
)
from .service import AttemptService, QuizService

QuizLimitDep = Depends(RateLimiter(times=20, seconds=60))
AttemptLimitDep = Depends(RateLimiter(times=20, seconds=60))


async def get_company_quiz_service(
    quiz_repo: QuizRepositoryDep,
    question_repo: QuestionRepositoryDep,
    member_service: CompanyMemberServiceDep,
) -> QuizService:
    return QuizService(
        quiz_repo=quiz_repo, question_repo=question_repo, member_service=member_service
    )


CompanyQuizServiceDep = Annotated[QuizService, Depends(get_company_quiz_service)]


async def get_attempt_service(
    attempt_repo: AttemptRepositoryDep,
    user_repo: UserRepositoryDep,
    answer_repo: AnswerRepositoryDep,
    question_repo: QuestionRepositoryDep,
    member_service: CompanyMemberServiceDep,
    quiz_service: CompanyQuizServiceDep,
) -> AttemptService:
    return AttemptService(
        attempt_repo=attempt_repo,
        user_repo=user_repo,
        answer_repo=answer_repo,
        question_repo=question_repo,
        member_service=member_service,
        quiz_service=quiz_service,
    )


AttemptServiceDep = Annotated[AttemptService, Depends(get_attempt_service)]


def get_quiz_repository(db: DBSessionDep) -> QuizRepository:
    return QuizRepository(db=db)


QuizRepositoryDep = Annotated[QuizRepository, Depends(get_quiz_repository)]


def get_question_repository(db: DBSessionDep) -> QuestionRepository:
    return QuestionRepository(db=db)


QuestionRepositoryDep = Annotated[QuestionRepository, Depends(get_question_repository)]


def get_attempt_repository(db: DBSessionDep) -> AttemptRepository:
    return AttemptRepository(db=db)


AttemptRepositoryDep = Annotated[AttemptRepository, Depends(get_attempt_repository)]


def get_answer_repository(db: DBSessionDep) -> AnswerRepository:
    return AnswerRepository(db=db)


AnswerRepositoryDep = Annotated[AnswerRepository, Depends(get_answer_repository)]
