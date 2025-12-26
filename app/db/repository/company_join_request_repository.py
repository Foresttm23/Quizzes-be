from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company_join_requests_model import CompanyJoinRequest as CompanyJoinRequestModel
from app.db.repository.base_repository import BaseRepository


class CompanyJoinRequestRepository(BaseRepository[CompanyJoinRequestModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyJoinRequestModel, db=db)
