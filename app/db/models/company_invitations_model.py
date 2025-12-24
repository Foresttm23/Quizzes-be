import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import UUID, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.postgres import Base
from app.utils.enum_utils import MessageStatus


class CompanyInvitation(Base):
    __tablename__ = "company_invitations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    invited_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[MessageStatus] = mapped_column(SQLEnum(MessageStatus, native_enum=True),
                                                  default=MessageStatus.PENDING)

    company: Mapped["Company"] = relationship(back_populates="invitations")
    invited_user: Mapped["User"] = relationship(back_populates="received_invitations")

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                          onupdate=func.now())

    __table_args__ = (
        sa.UniqueConstraint("company_id", "invited_user_id"),
    )
