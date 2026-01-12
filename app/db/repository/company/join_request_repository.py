from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company.join_request_model import (JoinRequest as CompanyJoinRequestModel)
from app.db.repository.base_repository import BaseRepository


class CompanyJoinRequestRepository(BaseRepository[CompanyJoinRequestModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyJoinRequestModel, db=db)
