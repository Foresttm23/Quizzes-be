import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy import UUID, DateTime, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.postgres import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # The str in "" syntax allows not importing every model needed.
    # SQLAlchemy will resolve it automatically if the User model exists
    members: Mapped[list["CompanyMember"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa.text('true'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                          onupdate=func.now())

    def __repr__(self) -> str:
        return f"<{self.id}>"
