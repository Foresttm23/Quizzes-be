# app/db/models/company/quiz/attempt_answer_model.py
import uuid

from sqlalchemy import ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.db.models.company.quiz.answer_option_model import AnswerOption
# from db.models.company.quiz.user_attempt.attempt_model import Attempt
# from app.db.models.company.quiz.question_model import Question
from app.db.postgres import Base


class AttemptAnswer(Base):
    __tablename__ = "quiz_attempt_answers"

    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("quiz_attempts.id", ondelete="CASCADE"))
    question_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("quiz_questions.id", ondelete="CASCADE"))
    # Can be None if user skipped or didn't answer.
    selected_option_id: Mapped[uuid.UUID | None] = mapped_column(UUID,
                                                                 ForeignKey("quiz_answer_options.id",
                                                                            ondelete="CASCADE"),
                                                                 nullable=True)

    attempt: Mapped["Attempt"] = relationship("Attempt", back_populates="answers")
    question: Mapped["Question"] = relationship("Question")
    selected_option: Mapped["AnswerOption"] = relationship("AnswerOption")
