from __future__ import annotations

from datetime import timedelta
from typing import Any, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from src.core.config import settings
from src.core.exceptions import (
    ExternalAuthProviderException,
    InstanceNotFoundException,
    InvalidJWTException,
    InvalidJWTRefreshException,
    InvalidPasswordException,
    PasswordReuseException,
    UserIncorrectPasswordOrEmailException,
)
from src.core.logger import logger
from src.core.schemas import PaginationResponse
from src.core.service import BaseService
from .enums import AuthProviderEnum, JWTTypeEnum
from .models import User as UserModel
from .repository import UserRepository
from .schemas import (
    JWTRefreshSchema,
    JWTSchema,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserDetailsResponse,
    UserInfoUpdateRequest,
    UserPasswordUpdateRequest,
)
from .utils import AuthUtils

SchemaType = TypeVar("SchemaType", bound=BaseModel)


class UserService(BaseService[UserRepository]):
    @property
    def display_name(self) -> str:
        return "User"

    def __init__(self, db: AsyncSession):
        super().__init__(repo=UserRepository(db=db))
        self.utils = AuthUtils()

    async def get_by_email_model(
            self, email: EmailStr, relationships: set[InstrumentedAttribute] | None = None
    ) -> UserModel:
        user = await self._get_user_by_field(
            field=UserModel.email, value=email, relationships=relationships
        )
        return user

    async def get_by_id_model(
            self, user_id: UUID, relationships: set[InstrumentedAttribute] | None = None
    ) -> UserModel:
        user = await self._get_user_by_field(
            field=UserModel.id, value=user_id, relationships=relationships
        )
        return user

    async def get_by_id(
            self, user_id: UUID, relationships: set[InstrumentedAttribute] | None = None
    ) -> UserDetailsResponse:
        user = await self._get_user_by_field(
            field=UserModel.id, value=user_id, relationships=relationships
        )
        return UserDetailsResponse.model_validate(user)

    async def _get_user_by_field(
        self,
        field: InstrumentedAttribute,
        value: Any,
        relationships: set[InstrumentedAttribute] | None = None,
    ) -> UserModel:
        user = await self.repo.get_instance_by_field_or_none(
            field=field, value=value, relationships=relationships
        )
        if not user:
            raise InstanceNotFoundException(instance_name=self.display_name)
        return user

    async def get_users_paginated(
            self, page: int, page_size: int
    ) -> PaginationResponse[UserDetailsResponse]:
        # We can now add filter fields.
        users_data = await self.repo.get_instances_paginated(
            page=page, page_size=page_size, return_schema=UserDetailsResponse
        )
        return users_data

    async def create_user_model(self, user_info: RegisterRequest) -> UserModel:
        """Method for creating a user"""
        # Since SecretStr(password) will transform to "***" with model_dump(),
        # we extract password before the call.
        plain_password = user_info.password.get_secret_value()
        hashed_password = self.utils.hash_password(password=plain_password)

        user_data = user_info.model_dump()
        user_data.pop("password")

        user = UserModel(id=uuid4(), **user_data, hashed_password=hashed_password)
        await self.repo.save_and_refresh(user)
        logger.info(
            f"Created new User: {user.id} auth_provider: {user.auth_provider} by system"
        )

        return user

    # Can be later renamed for something like create_user_from_external_jwt if we would have many providers.
    async def create_user_from_auth0(
            self, user_id: UUID, user_info: JWTSchema
    ) -> UserModel:
        """Method for creating a user from a jwt token"""
        # Since username is unique, we would need to create a unique username
        # relying only on email will expose it, so a simple uuid is better
        user = UserModel(
            id=user_id,
            email=user_info.email,  # .hex pretty much cleans the uuid from unique characters
            username=f"user_{uuid4().hex}",  # full UUID just to be sure
            hashed_password=None,
            auth_provider=user_info.auth_provider,
        )

        await self.repo.save_and_refresh(user)
        logger.info(
            f"Created new User: {user.id} auth_provider: {user.auth_provider} by system"
        )

        return user

    async def update_user_info(
            self, user: UserModel, new_user_info: UserInfoUpdateRequest
    ) -> UserModel:
        """Method for updating user details by id"""
        user = self._update_instance(instance=user, new_data=new_user_info, by=user.id)
        await self.repo.save_and_refresh(user)
        logger.info(f"Updated {self.display_name}: {user.id} by system")

        return user

    async def update_user_password(
            self, user: UserModel, new_password_info: UserPasswordUpdateRequest
    ) -> UserModel:
        """Method for updating user password by id"""
        self._verify_and_update_password(user=user, new_password_info=new_password_info)
        await self.repo.save_and_refresh(user)

        logger.info(f"{self.display_name}: {user.id} updated")
        logger.debug(f"{self.display_name}: {user.id} changed password")

        return user

    def _verify_and_update_password(
            self, user: UserModel, new_password_info: UserPasswordUpdateRequest
    ) -> None:
        current_password = new_password_info.current_password.get_secret_value()
        new_password = new_password_info.new_password.get_secret_value()

        if current_password == new_password:
            raise PasswordReuseException()

        if user.hashed_password is None:
            raise ExternalAuthProviderException(
                auth_provider=user.auth_provider, message="Incorrect Route"
            )

        if not self.utils.verify_password(
                plain_password=current_password, hashed_password=user.hashed_password
        ):
            raise InvalidPasswordException()

        user.hashed_password = self.utils.hash_password(password=new_password)

    async def delete_user(self, user: UserModel) -> None:
        await self._delete_instance(instance=user)
        await self.repo.save_and_refresh()


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.auth_utils = AuthUtils()

    async def register_user(self, sign_up_data: RegisterRequest) -> UserModel:
        """
        Wrapper for user_service.create_user.
        Can be expanded in the future.
        """
        user = await self.user_service.create_user_model(user_info=sign_up_data)
        return user

    async def handle_jwt_sign_in(
            self, jwt_payload: JWTSchema
    ) -> UserModel:  # TODO Return id or instance if asked.
        """Creates user from jwt if not found. Returns user in either way."""
        auth_provider = jwt_payload.auth_provider
        if auth_provider != AuthProviderEnum.LOCAL:
            user_id = self.auth_utils.generate_user_id_from_auth0(
                auth0_sub=jwt_payload.sub
            )
        else:
            user_id = UUID(jwt_payload.sub)

        try:
            user = await self.user_service.get_by_id_model(user_id=user_id)
        except InstanceNotFoundException:
            # Since user cannot possibly have a local JWT without already creating a user instance.
            user = await self.user_service.create_user_from_auth0(
                user_id=user_id, user_info=jwt_payload
            )

        return user

    async def handle_email_password_sign_in(
            self, sign_in_data: LoginRequest
    ) -> UserModel:
        """Creates user from password and email if not found. Returns user in either way."""
        # Checks if user exist byt itself, so the call checking user isn't needed
        # but might help in some unexpected situations
        try:
            user = await self.user_service.get_by_email_model(email=sign_in_data.email)
        except InstanceNotFoundException:
            raise UserIncorrectPasswordOrEmailException()

        if user.hashed_password is None:
            raise ExternalAuthProviderException(
                auth_provider=user.auth_provider, message="Incorrect Route"
            )

        plain_password = sign_in_data.password.get_secret_value()
        if not self.auth_utils.verify_password(
                plain_password=plain_password, hashed_password=user.hashed_password
        ):
            raise UserIncorrectPasswordOrEmailException()

        return user


class TokenService:
    def __init__(self):
        self.auth_utils = AuthUtils()

    def create_token_pairs(self, user: UserModel) -> TokenResponse:
        # user: UserModel = await self.user_service.fetch_user(field_name="id", field_value=user_id)
        access_token = self._create_access_token(user=user)
        refresh_token = self._create_refresh_token(user=user)

        result = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

        logger.debug(result)
        return TokenResponse.model_validate(result)

    async def verify_token_and_get_payload(self, jwt_token: str) -> JWTSchema:
        # Since we have 2 variation of registration we check them in order
        try:
            payload_dict = self.auth_utils.verify_local_token_and_get_payload(jwt_token)
        except InvalidJWTException:
            # If this raises error, code stops
            payload_dict = await self.auth_utils.verify_auth0_token_and_get_payload(
                jwt_token
            )

        return JWTSchema.model_validate(payload_dict)

    def verify_refresh_token_and_get_payload(self, token: str) -> JWTRefreshSchema:
        payload_dict = self.auth_utils.verify_refresh_token_and_get_payload(token)
        payload = JWTRefreshSchema.model_validate(payload_dict)
        if payload.type != JWTTypeEnum.REFRESH:
            raise InvalidJWTRefreshException()
        return payload

    def _create_access_token(self, user: UserModel) -> str:
        """Creates a signed JWT access token."""
        token_data = JWTSchema(
            sub=str(user.id), email=user.email, auth_provider=user.auth_provider
        )
        expires_delta = timedelta(
            minutes=settings.LOCAL_JWT.LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES
        )

        data = token_data.model_dump()
        encoded_jwt = self.auth_utils.create_access_token(
            data=data, expires_delta=expires_delta
        )
        return encoded_jwt

    def _create_refresh_token(self, user: UserModel) -> str:
        """Creates a signed JWT access token."""
        data = {"sub": str(user.id)}
        expires_delta = timedelta(
            days=settings.LOCAL_JWT.LOCAL_REFRESH_TOKEN_EXPIRE_DAYS
        )

        encoded_jwt = self.auth_utils.create_refresh_token(
            data=data, expires_delta=expires_delta
        )

        return encoded_jwt
