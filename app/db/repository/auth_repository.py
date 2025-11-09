from datetime import datetime, timezone, timedelta
from uuid import UUID

import requests
from jose import JWTError, jws, JWSError
from jose import jwt

from app.core.config import settings
from app.core.exceptions import InvalidJWTException


class AuthRepository:
    def __init__(self):
        pass

    # Later we can create a "task" that would every hour fetch keys from the endpoint
    # Or a simple variable with time or even Redis caching.
    @staticmethod
    def _fetch_jwks() -> list[dict]:
        return requests.get(settings.AUTH0_JWT.AUTH0_JWKS_ENDPOINT).json()["keys"]

    def _find_public_key(self, kid: str) -> dict | None:
        for key in self._fetch_jwks():
            if key["kid"] == kid:
                return key
        return None

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta) -> str:
        """Creates a signed JWT access token."""
        expire = datetime.now(timezone.utc) + expires_delta
        data.update({"exp": expire})

        encoded_jwt = jwt.encode(data, settings.LOCAL_JWT.LOCAL_JWT_SECRET,
                                 algorithm=settings.LOCAL_JWT.LOCAL_JWT_ALGORITHM)

        return encoded_jwt

    @staticmethod
    def _check_jwt_fields(response: dict):
        for key, value in response.items():
            if value is None:
                raise InvalidJWTException()

    @staticmethod
    def _fill_jwt_fields_from_payload(payload: dict):
        user_id: UUID = payload.get("id")
        email: str = payload.get("email")
        auth_provider: str = payload.get("auth_provider")

        return {"id": user_id, "email": email, "auth_provider": auth_provider}

    def verify_local_token_and_get_payload(self, token: str) -> dict:
        try:
            # Decode handles expiration automatically
            payload = jwt.decode(token, settings.LOCAL_JWT.LOCAL_JWT_SECRET,
                                 algorithms=[settings.LOCAL_JWT.LOCAL_JWT_ALGORITHM])
        except JWTError:
            raise InvalidJWTException()

        response = self._fill_jwt_fields_from_payload(payload=payload)
        self._check_jwt_fields(response)

        return response

    def verify_auth0_token_and_get_payload(self, token: str):
        try:
            unverified_token = jws.get_unverified_header(token)
            public_key = self._find_public_key(unverified_token["kid"])
            if public_key is None:
                raise InvalidJWTException()

            # Decode handles expiration automatically
            payload = jwt.decode(token=token, key=public_key, audience=settings.AUTH0_JWT.AUTH0_JWT_AUDIENCE,
                                 algorithms=settings.AUTH0_JWT.AUTH0_JWT_ALGORITHM, )
        except (JWTError, JWSError, KeyError):
            raise InvalidJWTException()

        # Since Auth0 only issue an email
        email: str = payload.get("email")
        response = {"email": email}
        self._check_jwt_fields(response)

        return response
