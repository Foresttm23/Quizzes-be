import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.db.models.user_model import User as UserModel
from app.db.repository.user_repository import UserRepository
from app.schemas.user_schemas.user_request_schema import SignUpRequest, UserInfoUpdateRequest, UserPasswordUpdateRequest
from app.services.base_service import BaseService
from app.utils.password_utils import hash_password


class UserService(BaseService[UserRepository]):
    @property
    def display_name(self) -> str:
        return "User"

    def __init__(self, db: AsyncSession):
        super().__init__(repo=UserRepository(db=db))

    async def fetch_user(self, field_name: str, field_value: Any) -> UserModel:
        user = await super()._fetch_instance(field_name=field_name, field_value=field_value)
        return user

    async def fetch_users_data_paginated(self, page: int, page_size: int) -> dict[..., list[UserModel]]:
        users_data = await super()._fetch_instances_data_paginated(page=page, page_size=page_size)
        return users_data

    async def create_user(self, user_info: SignUpRequest) -> UserModel:
        """Method for creating a user"""
        plain_password = user_info.password.get_secret_value()
        hashed_password = hash_password(plain_password)

        # Since we don't want to commit real password from the user_info fields
        # We specify directly what fields we need
        user = UserModel(email=user_info.email, username=user_info.username, hashed_password=hashed_password)

        await self.repo.save_changes_and_refresh(instance=user)

        logger.info(f"Created new User: {user.id} auth_provider: {user.auth_provider}")

        return user

    async def create_user_from_jwt(self, user_info: dict) -> UserModel:
        """Method for creating a user from a jwt token"""
        # Since username is unique, we would need to create a unique username
        # relying only on email will expose it, so a simple uuid is better
        user = UserModel(email=user_info["email"],  # .hex pretty much cleans the uuid from unique characters
                         username=f"user_{uuid.uuid4().hex[:12]}", hashed_password=None, auth_provider="auth0")

        await self.repo.save_changes_and_refresh(instance=user)

        logger.info(f"Created new User: {user.id} auth_provider: {user.auth_provider}")

        return user

    async def update_user_info(self, user_id: uuid.UUID, new_user_info: UserInfoUpdateRequest) -> UserModel:
        """Method for updating user details by id"""
        user = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=user_id)
        user = await super()._update_instance(instance=user, new_data=new_user_info)
        return user

    async def update_user_password(self, user_id: uuid.UUID, new_password_info: UserPasswordUpdateRequest) -> UserModel:
        """Method for updating user password by id"""
        user = await self.repo.get_instance_by_field_or_404(field_name="id", field_value=user_id)
        password_changed = self.repo.apply_password_updates(instance=user, new_password_info=new_password_info)

        if not password_changed:
            return user

        await self.repo.save_changes_and_refresh(instance=user)

        logger.info(f"{self.display_name}: {user.id} updated")
        logger.debug(f"{self.display_name}: {user.id} changed password")

        return user

    async def delete_user_by_id(self, user_id: uuid.UUID) -> None:
        await super()._delete_instance_by_id(instance_id=user_id)
