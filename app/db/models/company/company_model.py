import sqlalchemy as sa
from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.db.models.company.invitation_model import Invitation
# from app.db.models.company.join_request_model import JoinRequest
# from app.db.models.company.member_model import Member
# from app.db.models.company.quiz.quiz_model import Quiz
from app.db.postgres import Base, TimestampMixin


# TODO selecting is bad for pagination thus should be used directly in the db query nad not in the model
class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa.text('true'))

    # The str in "" syntax allows not importing every model needed.
    # SQLAlchemy will resolve it automatically if the User model exists
    members: Mapped[list["Member"]] = relationship("Member", back_populates="company", cascade="all, delete",
                                                   passive_deletes=True, lazy="selectin")
    join_requests: Mapped[list["JoinRequest"]] = relationship("JoinRequest", back_populates="company",
                                                              cascade="all, delete", passive_deletes=True,
                                                              lazy="selectin")
    invitations: Mapped[list["Invitation"]] = relationship("Invitation", back_populates="company",
                                                           cascade="all, delete", passive_deletes=True, lazy="selectin")
    quizzes: Mapped[list["Quiz"]] = relationship("Quiz", back_populates="company", cascade="all, delete",
                                                 passive_deletes=True)
