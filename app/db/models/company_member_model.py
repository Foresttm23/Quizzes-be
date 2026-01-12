import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy import UUID, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.postgres import Base
from app.utils.enum_utils import CompanyRole


class CompanyMember(Base):
    __tablename__ = "company_members"

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    role: Mapped[CompanyRole] = mapped_column(sa.Integer, default=CompanyRole.MEMBER)

    joined_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="companies")
