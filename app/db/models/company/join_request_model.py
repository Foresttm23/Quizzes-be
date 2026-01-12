import uuid

import sqlalchemy as sa
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# from app.db.models.company.company_model import Company
# from app.db.models.user_model import User
from app.db.postgres import Base, TimestampMixin
from app.utils.enum_utils import MessageStatus


class JoinRequest(Base, TimestampMixin):
    __tablename__ = "company_join_requests"

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
                                                  nullable=False, )
    requesting_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),
                                                          ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[MessageStatus] = mapped_column(SQLEnum(MessageStatus, native_enum=True),
                                                  default=MessageStatus.PENDING)

    company: Mapped["Company"] = relationship("Company", back_populates="join_requests")
    requesting_user: Mapped["User"] = relationship("User", back_populates="join_requests")

    __table_args__ = (sa.UniqueConstraint("company_id", "requesting_user_id"),)
