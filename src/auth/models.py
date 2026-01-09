from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models import Base, TimestampMixin

from .enums import AuthProviderEnum

if TYPE_CHECKING:
    from src.company.models import Invitation, JoinRequest
    from src.quiz.models import QuizAttempt


class User(Base, TimestampMixin):
    __tablename__ = "user"

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    auth_provider: Mapped[AuthProviderEnum] = mapped_column(
        SQLEnum(AuthProviderEnum, native_enum=False),
        default=AuthProviderEnum.LOCAL,
        server_default=AuthProviderEnum.LOCAL.value,
    )
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    last_quiz_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # lazy="selectin", allows for efficient access for all the relationships.
    # By making a separate query for each of them.
    # The default "select", creates a different query when a relationship is asked.
    companies: Mapped[list["Member"]] = relationship(  # pyright: ignore[reportUndefinedVariable]  # noqa: F821
        "Member",
        back_populates="user",
        cascade="all, delete",
        passive_deletes=True,
    )
    join_requests: Mapped[list["JoinRequest"]] = relationship(
        "JoinRequest",
        back_populates="requesting_user",
        cascade="all, delete",
        passive_deletes=True,
    )
    received_invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation",
        back_populates="invited_user",
        cascade="all, delete",
        passive_deletes=True,
    )
    attempts: Mapped[list["QuizAttempt"]] = relationship(
        "QuizAttempt",
        back_populates="user",
        passive_deletes=True,
        cascade="all, delete",
    )

    def __repr__(self) -> str:
        """Made for safe logging of a user if needed or made by accident"""
        return f"<{self.id!r}>"

    def to_dict(self) -> dict:
        """Transform main fields of User Model into dict"""
        return {
            "sub": str(self.id),
            "email": self.email,
            "username": self.username,
            "auth_provider": self.auth_provider,
            "is_banned": self.is_banned,
        }
