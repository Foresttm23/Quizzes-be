import datetime
import uuid

from sqlalchemy import UUID, DateTime, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.models.relationships import company_admins
from app.db.postgres import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str | None] = mapped_column(String, nullable=True)
    auth_provider: Mapped[str] = mapped_column(String, default="local")

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owned_companies: Mapped[list["Company"]] = relationship("Company", back_populates="owner", lazy="selectin")

    admin_companies: Mapped[list["Company"]] = relationship("Company", secondary=company_admins,
                                                            back_populates="admins", lazy="selectin")

    def __repr__(self) -> str:
        """Made for safe logging of a user if needed or made by accident"""
        return f"<{self.id!r}>"
