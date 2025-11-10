from sqlalchemy import UUID, ForeignKey, Table, Column

from app.db.postgres import Base

company_admins = Table("company_admins", Base.metadata,
                       Column("company_id", UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
                              primary_key=True),
                       Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
                              primary_key=True))
