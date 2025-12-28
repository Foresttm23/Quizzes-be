# app/db/models/company/quiz/question_model.py
import uuid

from sqlalchemy import ForeignKey, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.db.models.company.quiz.answer_option_model import AnswerOption
# from app.db.models.company.quiz.quiz_model import Quiz
from app.db.postgres import Base, TimestampMixin


class Question(Base, TimestampMixin):
    __tablename__ = "quiz_questions"

    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("company_quizzes.id", ondelete="CASCADE"))

    text: Mapped[str] = mapped_column(Text)

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    options: Mapped[list["AnswerOption"]] = relationship("AnswerOption", back_populates="question",
                                                         cascade="all, delete-orphan", lazy="selectin")
