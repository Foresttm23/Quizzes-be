import uuid

from sqlalchemy import ForeignKey, Text, UUID
from sqlalchemy import Integer, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import column_property
from sqlalchemy.sql import func

# from app.db.models.company.company_model import Company
from app.db.postgres import Base, TimestampMixin


class Quiz(Base, TimestampMixin):
    __tablename__ = "company_quizzes"

    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id", ondelete="CASCADE"))

    description: Mapped[str] = mapped_column(Text)
    allowed_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None = Unlimited

    company: Mapped["Company"] = relationship("Company", back_populates="quizzes")
    attempts: Mapped[list["Attempt"]] = relationship("Attempt", back_populates="quiz", passive_deletes=True,
                                                     cascade="all, delete")
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="quiz", passive_deletes=True)


from app.db.models.company.quiz.user_attempt.attempt_model import Attempt
from app.db.models.company.quiz.question_model import Question

Quiz.total_attempts = column_property(
    select(func.count(Attempt.id))
    .where(Attempt.quiz_id == Quiz.id)
    .correlate_except(Attempt)
    .scalar_subquery()
)

Quiz.questions_count = column_property(
    select(func.count(Question.id))
    .where(Question.quiz_id == Quiz.id)
    .correlate_except(Question)
    .scalar_subquery()
)
