from datetime import timedelta

from app.core.config import settings
from app.core.exceptions import InvalidJWTException
from app.core.exceptions import UserIncorrectPasswordOrEmailException, InstanceNotFoundException
from app.db.models.user_model import User as UserModel
from app.db.repository.auth_repository import AuthRepository
from app.schemas.user_schemas.user_request_schema import SignInRequest
from app.services.user_service import UserService
from app.utils.password_utils import verify_password


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.repo = AuthRepository()

    def verify_token_and_get_payload(self, jwt_token: str) -> dict:
        # Since we have 2 variation of registration we check them in order
        try:
            # Local verification is used for all auth endpoints,
            # thus should be first in order
            return self.repo.verify_local_token_and_get_payload(jwt_token)
        except InvalidJWTException:
            # If this raises error, code stops
            return self.repo.verify_auth0_token_and_get_payload(jwt_token)

    async def handle_jwt_sign_in(self, jwt_payload: dict):
        try:
            user = await self.user_service.fetch_user(field_name="email", field_value=jwt_payload["email"])
        except InstanceNotFoundException:
            user = await self.user_service.create_user_from_jwt(user_info=jwt_payload)

        return user

    def create_access_token(self, user: UserModel) -> str:
        """Creates a signed JWT access token."""
        data = {"id": str(user.id), "email": user.email, "auth_provider": user.auth_provider}
        expires_delta = timedelta(minutes=settings.LOCAL_JWT.LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES)

        encoded_jwt = self.repo.create_access_token(data=data, expires_delta=expires_delta)

        return encoded_jwt

    async def handle_email_password_sign_in(self, sign_in_data: SignInRequest):
        # Checks if user exist byt itself, so the call checking user isn't needed
        # but might help in some unexpected situations
        try:
            user = await self.user_service.fetch_user(field_name="email", field_value=sign_in_data.email)
        except InstanceNotFoundException:
            raise UserIncorrectPasswordOrEmailException()

        plain_password = sign_in_data.password.get_secret_value()
        if not user or not verify_password(plain_password, user.hashed_password):
            raise UserIncorrectPasswordOrEmailException()

        return user
