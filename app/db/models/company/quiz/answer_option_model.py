# app/db/models/company/quiz/answer_option_model.py
import uuid

from sqlalchemy import ForeignKey, Boolean, UUID, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.db.models.company.quiz.question_model import Question
from app.db.postgres import Base


class AnswerOption(Base):
    __tablename__ = "quiz_answer_options"

    question_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("quiz_questions.id", ondelete="CASCADE"))

    text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    question: Mapped["Question"] = relationship("Question", back_populates="options")

    def clone(self) -> "AnswerOption":
        return AnswerOption(id=uuid.uuid4(), text=self.text, is_correct=self.is_correct)
