import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy import UUID, DateTime, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.models.relationships import company_admins
from app.db.postgres import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    # Allows getting the whole owner as object
    # The backref allows calling user.owned_companies to get list of companies he owns
    owner: Mapped["User"] = relationship("User", back_populates="owned_companies")

    # The str in "" syntax allows not importing every model needed.
    # SQLAlchemy will resolve it automatically if the User model exists
    # lazy="selectin", allows for efficient access for all the relationships.
    # By making a separate query for each of them.
    # The default "select", creates a different query when a relationship is asked. (compony.admins)
    admins: Mapped[list["User"]] = relationship("User", secondary=company_admins, back_populates="admin_companies",
                                                lazy="selectin")

    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa.text('true'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                          onupdate=func.now())

    def __repr__(self) -> str:
        return f"<{self.id}>"
