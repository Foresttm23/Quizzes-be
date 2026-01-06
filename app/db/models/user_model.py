from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    auth_provider: Mapped[str] = mapped_column(String, default="local")
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    # lazy="selectin", allows for efficient access for all the relationships.
    # By making a separate query for each of them.
    # The default "select", creates a different query when a relationship is asked.
    companies: Mapped[list["Member"]] = relationship("Member", back_populates="user", cascade="all, delete",
                                                     passive_deletes=True)
    join_requests: Mapped[list["JoinRequest"]] = relationship("JoinRequest", back_populates="requesting_user",
                                                              cascade="all, delete", passive_deletes=True, )
    received_invitations: Mapped[list["Invitation"]] = relationship("Invitation", back_populates="invited_user",
                                                                    cascade="all, delete", passive_deletes=True, )
    attempts: Mapped[list["Attempt"]] = relationship("Attempt", back_populates="user", passive_deletes=True,
                                                     cascade="all, delete")

    def __repr__(self) -> str:
        """Made for safe logging of a user if needed or made by accident"""
        return f"<{self.id!r}>"

    def to_dict(self) -> dict:
        """Transform main fields of User Model into dict"""
        return {"id": str(self.id), "email": self.email, "username": self.username, "auth_provider": self.auth_provider,
                "is_banned": self.is_banned, }
