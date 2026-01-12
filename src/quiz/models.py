import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models import AttemptMixin, Base, TimestampMixin
from .enums import AttemptStatus

if TYPE_CHECKING:
    from src.auth.models import User
    from src.company.models import Company


class CompanyQuiz(Base, TimestampMixin):
    __tablename__ = "company_quiz"

    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("company.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    allowed_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True, default=1440)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=False)

    root_quiz_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("company_quiz.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="quizzes")

    attempts: Mapped[list["QuizAttempt"]] = relationship(
        "QuizAttempt",
        back_populates="quiz",
        passive_deletes=True,
        cascade="all, delete",
    )

    questions: Mapped[list["CompanyQuizQuestion"]] = relationship(
        "CompanyQuizQuestion",
        back_populates="quiz",
        passive_deletes=True,
        cascade="all, delete",
    )


class CompanyQuizQuestion(Base, TimestampMixin):
    __tablename__ = "company_quiz_question"

    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("company_quiz.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    points: Mapped[float] = mapped_column(Float, default=1)

    quiz: Mapped["CompanyQuiz"] = relationship("CompanyQuiz", back_populates="questions")
    options: Mapped[list["QuestionAnswerOption"]] = relationship(
        "QuestionAnswerOption",
        back_populates="question",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def clone(self) -> "CompanyQuizQuestion":
        return CompanyQuizQuestion(
            id=uuid.uuid4(),
            text=self.text,
            options=[opt.clone() for opt in self.options],
        )


class QuestionAnswerOption(Base):
    __tablename__ = "question_answer_option"

    question_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("company_quiz_question.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    question: Mapped["CompanyQuizQuestion"] = relationship("CompanyQuizQuestion", back_populates="options")

    def clone(self) -> "QuestionAnswerOption":
        return QuestionAnswerOption(id=uuid.uuid4(), text=self.text, is_correct=self.is_correct)


class QuizAttempt(Base, AttemptMixin):
    __tablename__ = "quiz_attempt"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("user.id", ondelete="CASCADE"))
    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("company_quiz.id", ondelete="CASCADE"))

    score: Mapped[float] = mapped_column(Float, default=0.0)
    correct_answers_count: Mapped[int] = mapped_column(Integer, default=0)
    total_questions_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[AttemptStatus] = mapped_column(
        SQLEnum(AttemptStatus, native_enum=False),
        default=AttemptStatus.IN_PROGRESS,
        server_default=AttemptStatus.IN_PROGRESS.value,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False

        return datetime.now(timezone.utc) >= self.expires_at

    quiz: Mapped["CompanyQuiz"] = relationship("CompanyQuiz", back_populates="attempts")
    user: Mapped["User"] = relationship("User", back_populates="attempts")

    answers: Mapped[list["QuizAttemptAnswer"]] = relationship(
        "QuizAttemptAnswer",
        back_populates="attempt",
        passive_deletes=True,
        cascade="all, delete",
    )


class QuizAttemptAnswer(Base):
    __tablename__ = "quiz_attempt_answer"

    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("quiz_attempt.id", ondelete="CASCADE"))
    question_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("company_quiz_question.id", ondelete="CASCADE"))

    attempt: Mapped["QuizAttempt"] = relationship("QuizAttempt", back_populates="answers")
    question: Mapped["CompanyQuizQuestion"] = relationship("CompanyQuizQuestion")

    selected_options: Mapped[list["AttemptAnswerSelection"]] = relationship(
        "AttemptAnswerSelection",
        back_populates="answer",
        cascade="all, delete",
        passive_deletes=True,
    )


class AttemptAnswerSelection(Base):
    __tablename__ = "attempt_answer_selection"

    answer_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("quiz_attempt_answer.id", ondelete="CASCADE"))
    option_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("question_answer_option.id", ondelete="CASCADE"))

    answer: Mapped["QuizAttemptAnswer"] = relationship("QuizAttemptAnswer", back_populates="selected_options")
    option: Mapped["QuestionAnswerOption"] = relationship("QuestionAnswerOption")
