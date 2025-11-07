from datetime import datetime, timezone
from datetime import timedelta

from jose import jwt

from app.core.config import settings
from app.core.exceptions import InvalidJWTToken


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
            raise InvalidJWTToken()
