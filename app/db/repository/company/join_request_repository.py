from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository.base_repository import BaseRepository
from db.models.company_models import (JoinRequest as CompanyJoinRequestModel)


class JoinRequestRepository(BaseRepository[CompanyJoinRequestModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyJoinRequestModel, db=db)
