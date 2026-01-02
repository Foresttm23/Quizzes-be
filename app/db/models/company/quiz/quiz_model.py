import uuid

from sqlalchemy import ForeignKey, Text, UUID, Boolean, String
from sqlalchemy import Integer, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import column_property
from sqlalchemy.sql import func

# from app.db.models.company.company_model import Company
from app.db.postgres import Base, TimestampMixin


class Quiz(Base, TimestampMixin):
    __tablename__ = "company_quizzes"

    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("companies.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    allowed_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None = Unlimited
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    # For the updated version.
    # If Admin or Owner updates the quiz, we display the latest version and hide the previous
    is_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    # Allows to get back to the old versions of the quizzes
    root_quiz_id: Mapped[UUID | None] = mapped_column(ForeignKey("quizzes.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="quizzes")
    attempts: Mapped[list["Attempt"]] = relationship("Attempt", back_populates="quiz", passive_deletes=True,
                                                     cascade="all, delete")
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="quiz", passive_deletes=True)


from app.db.models.company.quiz.attempt.attempt_model import Attempt
from app.db.models.company.quiz.question_model import Question

Quiz.total_attempts = column_property(
    select(func.count(Attempt.id)).where(Attempt.quiz_id == Quiz.id).correlate_except(Attempt).scalar_subquery())

Quiz.questions_count = column_property(
    select(func.count(Question.id)).where(Question.quiz_id == Quiz.id).correlate_except(Question).scalar_subquery())
