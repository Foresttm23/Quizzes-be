from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository.base_repository import BaseRepository
from db.models.company_models import Company as CompanyModel


class CompanyRepository(BaseRepository[CompanyModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyModel, db=db)
