import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.security import hash_password
from app.db.models.user_model import User as UserModel
from app.db.repository.user_repository import UserRepository
from app.schemas.user_schema import SignUpRequest, UserInfoUpdateRequest, UserPasswordUpdateRequest
from app.services.base_service import BaseService


class UserService(BaseService[UserRepository]):
    @property
    def display_name(self) -> str:
        return "User"

    def __init__(self, db: AsyncSession):
        super().__init__(repo=UserRepository(db=db))

    async def create_user(self, user_info: SignUpRequest):
        """Method for creating a user"""
        plain_password = user_info.password.get_secret_value()
        hashed_password = hash_password(plain_password)

        # Since we don't want to commit real password from the user_info fields
        # We specify directly what fields we need
        user = UserModel(
            email=user_info.email,
            username=user_info.username,
            hashed_password=hashed_password
        )

        await self.repo.save_changes_and_refresh(instance=user)

        logger.info(f"Created new User: {user.id}")

        return user

    async def update_user_info(self, user_id: uuid.UUID, new_user_info: UserInfoUpdateRequest):
        """Method for updating user details by id"""
        user = await super()._update_instance(instance_id=user_id, new_data=new_user_info)
        return user

    async def update_user_password(self, user_id: uuid.UUID, new_password_info: UserPasswordUpdateRequest):
        """Method for updating user password by id"""
        user = await self.repo.get_instance_or_404(instance_id=user_id)
        password_changed = self.repo.apply_password_updates(instance=user, new_password_info=new_password_info)

        if not password_changed:
            return user

        await self.repo.save_changes_and_refresh(instance=user)

        logger.info(f"{self.display_name}: {user.id} updated")
        logger.debug(f"{self.display_name}: {user.id} changed password")

        return user
