from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company.company_model import Company as CompanyModel
from app.db.repository.base_repository import BaseRepository


class CompanyRepository(BaseRepository[CompanyModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyModel, db=db)
