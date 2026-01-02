from typing import TypeVar, Any
from uuid import uuid4, UUID

from app.schemas.user_schemas.user_request_schema import RegisterRequest, UserInfoUpdateRequest
from app.schemas.user_schemas.user_request_schema import UserPasswordUpdateRequest
from pydantic import BaseModel
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.exceptions import InvalidPasswordException, InstanceNotFoundException
from app.core.exceptions import PasswordReuseException
from app.core.logger import logger
from app.schemas.base_schemas import PaginationResponse
from app.services.base_service import BaseService
from app.utils.password_utils import hash_password, verify_password
from db.models.user.user_model import User as UserModel
from db.repository.user.user_repository import UserRepository

SchemaType = TypeVar("SchemaType", bound=BaseModel)


class UserService(BaseService[UserRepository]):
    @property
    def display_name(self) -> str:
        return "User"

    def __init__(self, db: AsyncSession):
        super().__init__(repo=UserRepository(db=db))

    async def get_by_email(self, email: EmailStr, relationships: set[InstrumentedAttribute] | None = None) -> UserModel:
        user = await self._get_user_by_field(field=UserModel.email, value=email, relationships=relationships)
        return user

    async def get_by_id(self, user_id: UUID, relationships: set[InstrumentedAttribute] | None = None) -> UserModel:
        user = await self._get_user_by_field(field=UserModel.id, value=user_id, relationships=relationships)
        return user

    async def _get_user_by_field(self, field: InstrumentedAttribute, value: Any,
                                 relationships: set[InstrumentedAttribute] | None = None) -> UserModel:
        user = await self.repo.get_instance_by_field_or_none(field=field, value=value, relationships=relationships)
        if not user:
            raise InstanceNotFoundException(instance_name=self.display_name)
        return user

    async def get_users_paginated(self, page: int, page_size: int) -> PaginationResponse[SchemaType]:
        # We can now add filter fields.
        users_data = await self.repo.get_instances_paginated(page=page, page_size=page_size)
        return users_data

    async def create_user(self, user_info: RegisterRequest) -> UserModel:
        """Method for creating a user"""
        # Since SecretStr(password) will transform to "***" with model_dump(),
        # we extract password before the call.
        plain_password = user_info.password.get_secret_value()
        hashed_password = hash_password(plain_password)

        user_data = user_info.model_dump()
        user_data.pop("password")

        # Since we don't want to commit real password from the user_info fields
        # We specify directly what fields we need
        user = UserModel(id=uuid4(), **user_data, hashed_password=hashed_password)

        await self.repo.save_and_refresh(user)
        logger.info(f"Created new User: {user.id} auth_provider: {user.auth_provider} by system")

        return user

    # Can be later renamed for something like create_user_from_external_jwt if we would have many providers.
    async def create_user_from_auth0(self, user_info: dict) -> UserModel:
        """Method for creating a user from a jwt token"""
        # Since username is unique, we would need to create a unique username
        # relying only on email will expose it, so a simple uuid is better
        user = UserModel(id=uuid4(), email=user_info["email"],
                         # .hex pretty much cleans the uuid from unique characters
                         username=f"user_{uuid4().hex[:12]}", hashed_password=None, auth_provider="auth0")

        await self.repo.save_and_refresh(user)
        logger.info(f"Created new User: {user.id} auth_provider: {user.auth_provider} by system")

        return user

    async def update_user_info(self, user: UserModel, new_user_info: UserInfoUpdateRequest) -> UserModel:
        """Method for updating user details by id"""
        user = self._update_instance(instance=user, new_data=new_user_info, by=user.id)
        await self.repo.save_and_refresh(user)
        logger.info(f"Updated {self.display_name}: {user.id} by system")

        return user

    async def update_user_password(self, user: UserModel, new_password_info: UserPasswordUpdateRequest) -> UserModel:
        """Method for updating user password by id"""
        self._verify_and_update_password(user=user, new_password_info=new_password_info)
        await self.repo.save_and_refresh(user)

        logger.info(f"{self.display_name}: {user.id} updated")
        logger.debug(f"{self.display_name}: {user.id} changed password")

        return user

    @staticmethod
    def _verify_and_update_password(user: UserModel, new_password_info: UserPasswordUpdateRequest) -> None:
        current_password = new_password_info.current_password.get_secret_value()
        new_password = new_password_info.new_password.get_secret_value()

        if current_password == new_password:
            raise PasswordReuseException()

        if not verify_password(current_password, user.hashed_password):
            raise InvalidPasswordException()

        user.hashed_password = hash_password(new_password)

    async def delete_user(self, user: UserModel) -> None:
        await self._delete_instance(instance=user)
        await self.repo.save_and_refresh()
