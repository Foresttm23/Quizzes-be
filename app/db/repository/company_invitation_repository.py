from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company_invitations_model import CompanyInvitation as CompanyInvitationModel
from app.db.repository.base_repository import BaseRepository


class CompanyInvitationRepository(BaseRepository[CompanyInvitationModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(model=CompanyInvitationModel, db=db)
