from uuid import UUID

from app.schemas.base_schemas import Base


class SaveAnswerRequestSchema(Base):
    ids: list[UUID]
