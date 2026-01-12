from datetime import timedelta

from app.core.config import settings
from app.core.exceptions import InvalidJWTException, InvalidJWTRefreshException
from app.core.exceptions import (UserIncorrectPasswordOrEmailException, InstanceNotFoundException, )
from app.core.logger import logger
from app.db.models.user.user_model import User as UserModel
from app.schemas.user.user_request_schema import LoginRequest, RegisterRequest
from app.services.user.user_service import UserService
from app.utils.auth_utils import AuthUtils
from app.utils.password_utils import verify_password


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.utils = AuthUtils()

    def create_token_pairs(self, user: UserModel):
        # user: UserModel = await self.user_service.fetch_user(field_name="id", field_value=user_id)
        access_token = self._create_access_token(user=user)
        refresh_token = self._create_refresh_token(user=user)

        logger.debug({"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", })
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", }

    async def register_user(self, sign_up_data: RegisterRequest) -> UserModel:
        """
        Wrapper for user_service.create_user.
        Can be expanded in the future.
        """
        user = await self.user_service.create_user(user_info=sign_up_data)
        return user

    def verify_token_and_get_payload(self, jwt_token: str) -> dict:
        # Since we have 2 variation of registration we check them in order
        try:
            return self.utils.verify_local_token_and_get_payload(jwt_token)
        except InvalidJWTException:
            # If this raises error, code stops
            return self.utils.verify_auth0_token_and_get_payload(jwt_token)

    def verify_local_token_and_get_payload(self, jwt_token: str) -> dict:
        return self.utils.verify_local_token_and_get_payload(token=jwt_token)

    async def handle_jwt_sign_in(self, jwt_payload: dict):
        """Creates user from jwt if not found. Returns user in either way."""
        try:
            user = await self.user_service.get_by_email(email=jwt_payload["email"])
        except InstanceNotFoundException:
            # Since user cannot possibly have a local JWT without already creating a user instance.
            user = await self.user_service.create_user_from_auth0(user_info=jwt_payload)

        return user

    def verify_refresh_token_and_get_payload(self, token: str) -> dict:
        payload = self.utils.verify_refresh_token_and_get_payload(token)
        if payload.get("type") != "refresh":
            raise InvalidJWTRefreshException()
        return payload

    def _create_access_token(self, user: UserModel) -> str:
        """Creates a signed JWT access token."""
        data = self.utils.fill_jwt_fields_from_dict(data=user.to_dict())
        expires_delta = timedelta(minutes=settings.LOCAL_JWT.LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES)

        encoded_jwt = self.utils.create_access_token(data=data, expires_delta=expires_delta)

        return encoded_jwt

    def _create_refresh_token(self, user: UserModel) -> str:
        """Creates a signed JWT access token."""
        data = {"id": str(user.id)}
        expires_delta = timedelta(minutes=settings.LOCAL_JWT.LOCAL_REFRESH_TOKEN_EXPIRE_DAYS)

        encoded_jwt = self.utils.create_refresh_token(data=data, expires_delta=expires_delta)

        return encoded_jwt

    async def handle_email_password_sign_in(self, sign_in_data: LoginRequest):
        """Creates user from password and email if not found. Returns user in either way."""
        # Checks if user exist byt itself, so the call checking user isn't needed
        # but might help in some unexpected situations
        try:
            user = await self.user_service.get_by_email(email=sign_in_data.email)
        except InstanceNotFoundException:
            raise UserIncorrectPasswordOrEmailException()

        plain_password = sign_in_data.password.get_secret_value()
        if not user or not verify_password(plain_password, user.hashed_password):
            raise UserIncorrectPasswordOrEmailException()

        return user
