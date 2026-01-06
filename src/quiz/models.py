import uuid

from sqlalchemy import Float, ForeignKey, Text, UUID, Boolean, String, Integer, select, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property
from sqlalchemy.sql import func

from core.models import Base, TimestampMixin, AttemptMixin
from .enums import AttemptStatus


class CompanyQuiz(Base, TimestampMixin):
    __tablename__ = "company_quiz"

    company_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("company.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    allowed_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=False)

    root_quiz_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("company_quiz.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="quizzes")

    attempts: Mapped[list["QuizAttempt"]] = relationship("QuizAttempt", back_populates="quiz", passive_deletes=True,
                                                         cascade="all, delete")

    questions: Mapped[list["CompanyQuizQuestion"]] = relationship("CompanyQuizQuestion", back_populates="quiz",
                                                                  passive_deletes=True, cascade="all, delete")


class CompanyQuizQuestion(Base, TimestampMixin):
    __tablename__ = "company_quiz_question"

    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("company_quiz.id", ondelete="CASCADE"))
    points: Mapped[float] = mapped_column(Float, default=1)
    text: Mapped[str] = mapped_column(Text)

    quiz: Mapped["CompanyQuiz"] = relationship("CompanyQuiz", back_populates="questions")
    options: Mapped[list["QuestionAnswerOption"]] = relationship("QuestionAnswerOption", back_populates="question",
                                                                 cascade="all, delete-orphan", passive_deletes=True)

    def clone(self) -> "CompanyQuizQuestion":
        return CompanyQuizQuestion(id=uuid.uuid4(), text=self.text, options=[opt.clone() for opt in self.options])


class QuestionAnswerOption(Base):
    __tablename__ = "company_quiz_question"

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
    status: Mapped[AttemptStatus] = mapped_column(SQLEnum(AttemptStatus), default=AttemptStatus.IN_PROGRESS)

    quiz: Mapped["CompanyQuiz"] = relationship("CompanyQuiz", back_populates="attempts")
    user: Mapped["User"] = relationship("User", back_populates="attempts")

    answers: Mapped[list["QuizAttemptAnswer"]] = relationship("QuizAttemptAnswer", back_populates="attempt",
                                                              passive_deletes=True, cascade="all, delete")


class QuizAttemptAnswer(Base):
    __tablename__ = "quiz_attempt_answer"

    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("quiz_attempt.id", ondelete="CASCADE"))
    question_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("company_quiz_question.id", ondelete="CASCADE"))

    attempt: Mapped["QuizAttempt"] = relationship("QuizAttempt", back_populates="answers")
    question: Mapped["CompanyQuizQuestion"] = relationship("CompanyQuizQuestion")

    selected_options: Mapped[list["AttemptAnswerSelection"]] = relationship("AttemptAnswerSelection",
                                                                            back_populates="answer",
                                                                            cascade="all, delete", passive_deletes=True)


class AttemptAnswerSelection(Base):
    __tablename__ = "attempt_answer_selection"

    answer_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("quiz_attempt_answer.id", ondelete="CASCADE"))
    option_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("company_quiz_question.id", ondelete="CASCADE"))

    answer: Mapped["QuizAttemptAnswer"] = relationship("QuizAttemptAnswer", back_populates="selected_options")
    option: Mapped["QuestionAnswerOption"] = relationship("QuestionAnswerOption")


CompanyQuiz.total_attempts = column_property(
    select(func.count(QuizAttempt.id)).where(QuizAttempt.quiz_id == CompanyQuiz.id).correlate_except(
        QuizAttempt).scalar_subquery())

CompanyQuiz.questions_count = column_property(
    select(func.count(CompanyQuizQuestion.id)).where(CompanyQuizQuestion.quiz_id == CompanyQuiz.id).correlate_except(
        CompanyQuizQuestion).scalar_subquery())
