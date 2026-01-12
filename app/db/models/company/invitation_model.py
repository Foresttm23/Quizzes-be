import uuid

import sqlalchemy as sa
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.db.models.company.company_model import Company
# from app.db.models.user_model import User
from app.db.postgres import Base, TimestampMixin
from app.utils.enum_utils import MessageStatus


class Invitation(Base, TimestampMixin):
    __tablename__ = "company_invitations"

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"))
    invited_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[MessageStatus] = mapped_column(SQLEnum(MessageStatus, native_enum=True),
                                                  default=MessageStatus.PENDING)

    company: Mapped["Company"] = relationship("Company", back_populates="invitations")
    invited_user: Mapped["User"] = relationship("User", back_populates="received_invitations")

    __table_args__ = (sa.UniqueConstraint("company_id", "invited_user_id"),)
