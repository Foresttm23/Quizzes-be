from datetime import datetime, timezone, timedelta
from uuid import UUID

import requests
from jose import JWTError, jws, JWSError, jwt

from app.core.config import settings
from app.core.exceptions import InvalidJWTException, InvalidJWTFieldsException


class AuthUtils:
    def __init__(self):
        pass

    def create_access_token(self, data: dict, expires_delta: timedelta) -> str:
        """Creates a signed JWT access token."""
        expire = datetime.now(timezone.utc) + expires_delta
        data.update({"exp": expire, "type": "access"})

        encoded_jwt = self._handle_local_token_encode(data=data)

        return encoded_jwt

    def verify_local_token_and_get_payload(self, token: str) -> dict:
        payload = self._handle_local_token_decode(token=token)

        response = self.fill_jwt_fields_from_dict(data=payload)

        return response

    def verify_auth0_token_and_get_payload(self, token: str):
        payload = self._handle_auth0_token_decode(token=token)

        # Since Auth0 only issue an email
        email: str = payload.get("email")
        response = {"email": email}
        self._check_jwt_fields(response)

        return response

    def create_refresh_token(self, data: dict, expires_delta: timedelta):
        expire = datetime.now(timezone.utc) + expires_delta
        data.update({"exp": expire, "type": "refresh"})
        encoded_jwt = self._handle_local_token_encode(data=data)

        return encoded_jwt

    def verify_refresh_token_and_get_payload(self, token: str):
        payload = self._handle_local_token_decode(token=token)
        return payload

    def fill_jwt_fields_from_dict(self, data: dict):
        user_id: UUID = data.get("id")
        email: str = data.get("email")
        auth_provider: str = data.get("auth_provider")

        response = {"id": str(user_id), "email": email, "auth_provider": auth_provider}
        self._check_jwt_fields(response=response)

        return response

    @staticmethod
    def _handle_local_token_encode(data: dict):
        encoded_jwt = jwt.encode(
            data,
            settings.LOCAL_JWT.LOCAL_JWT_SECRET,
            algorithm=settings.LOCAL_JWT.LOCAL_JWT_ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def _handle_local_token_decode(token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                settings.LOCAL_JWT.LOCAL_JWT_SECRET,
                algorithms=[settings.LOCAL_JWT.LOCAL_JWT_ALGORITHM],
            )
        except JWTError:
            raise InvalidJWTException()

        return payload

    def _handle_auth0_token_decode(self, token: str) -> dict:
        try:
            unverified_token = jws.get_unverified_header(token)
            public_key = self._find_public_key(unverified_token["kid"])
            if public_key is None:
                raise InvalidJWTException()

            payload = jwt.decode(token=token, key=public_key, audience=settings.AUTH0_JWT.AUTH0_JWT_AUDIENCE,
                                 algorithms=settings.AUTH0_JWT.AUTH0_JWT_ALGORITHM, )
        except (JWTError, JWSError, KeyError):
            raise InvalidJWTException()

        return payload

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
    def _check_jwt_fields(response: dict):
        for key, value in response.items():
            if value is None:
                raise InvalidJWTFieldsException()
