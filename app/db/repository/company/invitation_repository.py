from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repository.base_repository import BaseRepository
from db.models.company_models import Invitation as CompanyInvitationModel


class InvitationRepository(BaseRepository[CompanyInvitationModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyInvitationModel, db=db)
