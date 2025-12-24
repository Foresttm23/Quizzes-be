import datetime
import uuid

from sqlalchemy import UUID, DateTime, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.postgres import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    auth_provider: Mapped[str] = mapped_column(String, default="local")
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    # lazy="selectin", allows for efficient access for all the relationships.
    # By making a separate query for each of them.
    # The default "select", creates a different query when a relationship is asked.
    companies: Mapped[list["CompanyMember"]] = relationship(back_populates="user", lazy="selectin")
    join_requests: Mapped[list["CompanyJoinRequest"]] = relationship(back_populates="requesting_user", lazy="selectin")

    received_invitations: Mapped[list["CompanyInvitation"]] = relationship(back_populates="invited_user",
                                                                           lazy="selectin")

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        """Made for safe logging of a user if needed or made by accident"""
        return f"<{self.id!r}>"

    def to_dict(self) -> dict:
        """Transform main fields of User Model into dict"""
        return {"id": str(self.id), "email": self.email, "username": self.username, "auth_provider": self.auth_provider,
                "is_banned": self.is_banned, }
