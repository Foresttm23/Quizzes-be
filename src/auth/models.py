from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.exceptions import (
    ExternalAuthProviderException,
    InvalidPasswordException,
    PasswordReuseException,
)
from src.core.models import Base, TimestampMixin

from .enums import AuthProviderEnum
from .security import hash_password, verify_password

if TYPE_CHECKING:
    from src.company.models import Invitation, JoinRequest, Member
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
    last_quiz_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    companies: Mapped[list["Member"]] = relationship(
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

    async def update_password(self, current_plain: str, new_plain: str):
        if current_plain == new_plain:
            raise PasswordReuseException()

        if self.hashed_password is None:
            raise ExternalAuthProviderException(
                auth_provider=self.auth_provider, message="Incorrect Route"
            )

        if not await verify_password(
            plain_password=current_plain, hashed_password=self.hashed_password
        ):
            raise InvalidPasswordException()

        self.hashed_password = await hash_password(password=new_plain)
