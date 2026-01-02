import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.postgres import Base


# TODO selecting is bad for pagination thus should be used directly in the db query nad not in the model
class Company(Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa.text('true'))

    # The str in "" syntax allows not importing every model needed.
    # SQLAlchemy will resolve it automatically if the User model exists
    members: Mapped[list["CompanyMember"]] = relationship(back_populates="company", cascade="all, delete-orphan",
                                                          lazy="selectin")
    join_requests: Mapped[list["CompanyJoinRequest"]] = relationship(back_populates="company",
                                                                     cascade="all, delete-orphan", lazy="selectin")
    invitations: Mapped[list["CompanyInvitation"]] = relationship(back_populates="company",
                                                                  cascade="all, delete-orphan", lazy="selectin")

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                          onupdate=func.now())

    def __repr__(self) -> str:
        return f"<{self.id}>"
