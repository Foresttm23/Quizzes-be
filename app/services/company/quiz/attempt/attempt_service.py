from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository.company.quiz.attempt.attempt_repository import QuizAttemptRepository
from app.services.base_service import BaseService
from app.services.company.member_service import CompanyMemberService


class AttemptService(BaseService[QuizAttemptRepository]):
    @property
    def display_name(self) -> str:
        return "QuizAttempt"

    def __init__(self, db: AsyncSession, company_member_service: CompanyMemberService):
        super().__init__(repo=QuizAttemptRepository(db=db))
        self.company_member_service = company_member_service
