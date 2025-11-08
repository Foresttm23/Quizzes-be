from datetime import datetime, timezone
from datetime import timedelta
from uuid import UUID

from jose import jwt

from app.core.config import settings
from app.core.exceptions import InvalidJWTException
from app.core.exceptions import UserIncorrectPasswordOrEmailException, InstanceNotFoundException
from app.schemas.user_schemas.user_request_schema import SignInRequest
from app.services.user_service import UserService
from app.utils.password_utils import verify_password


def create_access_token(data: dict, expires_delta: timedelta) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.LOCAL_JWT.LOCAL_JWT_SECRET,
                             algorithm=settings.LOCAL_JWT.LOCAL_JWT_ALGORITHM)

    return encoded_jwt


def check_jwt_fields(response: dict):
    for key, value in response.items():
        if value is None:
            raise InvalidJWTException()


def fill_jwt_fields_from_payload(payload: dict):
    user_id: UUID = payload.get("id")
    email: str = payload.get("email")
    auth_provider: str = payload.get("auth_provider")

    return {"id": user_id, "email": email, "auth_provider": auth_provider}


async def handle_jwt_sign_in(user_service: UserService, jwt_payload: dict):
    try:
        user = await user_service.fetch_instance(field_name="email", field_value=jwt_payload["email"])
    except InstanceNotFoundException:
        user = await user_service.create_user_from_jwt(user_info=jwt_payload)

    return user


async def handle_email_password_sign_in(user_service: UserService, sign_in_data: SignInRequest):
    # Checks if user exist byt itself, so the call checking user isn't needed
    # but might help in some unexpected situations
    user = await user_service.fetch_instance(field_name="email", field_value=sign_in_data.email)

    plain_password = sign_in_data.password.get_secret_value()
    if not user or not verify_password(plain_password, user.hashed_password):
        raise UserIncorrectPasswordOrEmailException()

    return user
