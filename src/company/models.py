import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy import DateTime, Enum as SQLEnum, String, Text, Boolean, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.models import Base, TimestampMixin
from .enums import CompanyRole, MessageStatus


class Company(Base, TimestampMixin):
    __tablename__ = "company"

    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa.text("true"))

    # The str in "" syntax allows not importing every model needed.
    # SQLAlchemy will resolve it automatically if the User model exists
    members: Mapped[list["Member"]] = relationship("Member", back_populates="company", cascade="all, delete",
                                                   passive_deletes=True)
    join_requests: Mapped[list["JoinRequest"]] = relationship("JoinRequest", back_populates="company",
                                                              cascade="all, delete", passive_deletes=True, )
    invitations: Mapped[list["Invitation"]] = relationship("Invitation", back_populates="company",
                                                           cascade="all, delete", passive_deletes=True, )
    quizzes: Mapped[list["CompanyQuiz"]] = relationship("CompanyQuiz", back_populates="company", cascade="all, delete",
                                                        passive_deletes=True)


class Member(Base):
    __tablename__ = "company_member"

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"))

    role: Mapped[CompanyRole] = mapped_column(sa.Integer, default=CompanyRole.MEMBER)
    joined_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship("Company", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="company")

    __table_args__ = (sa.UniqueConstraint("company_id", "user_id"),)


class Invitation(Base, TimestampMixin):
    __tablename__ = "company_invitation"

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"))
    invited_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"))
    status: Mapped[MessageStatus] = mapped_column(SQLEnum(MessageStatus, native_enum=False),
                                                  default=MessageStatus.PENDING,
                                                  server_default=MessageStatus.PENDING.value)

    company: Mapped["Company"] = relationship("Company", back_populates="invitations")
    invited_user: Mapped["User"] = relationship("User", back_populates="received_invitations")

    __table_args__ = (sa.UniqueConstraint("company_id", "invited_user_id"),)


class JoinRequest(Base, TimestampMixin):
    __tablename__ = "company_join_request"

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"),
                                                  nullable=False, )
    requesting_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"),
                                                          nullable=False)
    status: Mapped[MessageStatus] = mapped_column(SQLEnum(MessageStatus, native_enum=False),
                                                  default=MessageStatus.PENDING,
                                                  server_default=MessageStatus.PENDING.value)

    company: Mapped["Company"] = relationship("Company", back_populates="join_requests")
    requesting_user: Mapped["User"] = relationship("User", back_populates="join_requests")

    __table_args__ = (sa.UniqueConstraint("company_id", "requesting_user_id"),)
