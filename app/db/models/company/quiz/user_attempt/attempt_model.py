import uuid

from sqlalchemy import ForeignKey, Float, Boolean, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.db.models.company.quiz.user_attempt.attempt_answer_model import AttemptAnswer
# from app.db.models.company.quiz.quiz_model import Quiz
# from app.db.models.user_model import User
from app.db.postgres import Base, TimestampMixin


class Attempt(Base, TimestampMixin):
    __tablename__ = "quiz_attempts"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id", ondelete="CASCADE"))
    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("company_quizzes.id", ondelete="CASCADE"))

    score_percent: Mapped[float] = mapped_column(Float, default=0.0)
    is_passed: Mapped[bool] = mapped_column(Boolean, default=False)

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="attempts")
    user: Mapped["User"] = relationship("User", back_populates="attempts")
    answers: Mapped[list["AttemptAnswer"]] = relationship("AttemptAnswer", back_populates="attempt",
                                                          passive_deletes=True, cascade="all, delete")
