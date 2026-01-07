from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid5

import httpx
from jose import JWTError, jws, JWSError, jwt
from pwdlib import PasswordHash

from src.auth.enums import JWTTypeEnum, AuthProviderEnum
from src.core.config import settings
from src.core.exceptions import InvalidJWTException


class AuthUtils:
    def __init__(self):
        self.pwd_hasher = PasswordHash.recommended()

    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_hasher.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify that hashed_password and plain_password are equal"""
        return self.pwd_hasher.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: timedelta) -> str:
        """Creates a signed JWT access token."""
        expire = datetime.now(timezone.utc) + expires_delta
        data.update({"exp": expire, "type": JWTTypeEnum.ACCESS, "auth_provider": AuthProviderEnum.LOCAL})

        encoded_jwt = self._handle_local_token_encode(data=data, secret_key=settings.LOCAL_JWT.LOCAL_JWT_SECRET)
        return encoded_jwt

    def verify_local_token_and_get_payload(self, token: str) -> dict:
        payload = self._handle_local_token_decode(token=token, secret_key=settings.LOCAL_JWT.LOCAL_JWT_SECRET)
        return payload

    async def verify_auth0_token_and_get_payload(self, token: str) -> dict:
        payload = await self._handle_auth0_token_decode(token=token)
        return payload

    def create_refresh_token(self, data: dict, expires_delta: timedelta) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        data.update({"exp": expire, "type": JWTTypeEnum.REFRESH})
        encoded_jwt = self._handle_local_token_encode(data=data,
                                                      secret_key=settings.LOCAL_JWT.LOCAL_REFRESH_TOKEN_SECRET)

        return encoded_jwt

    def verify_refresh_token_and_get_payload(self, token: str) -> dict:
        payload = self._handle_local_token_decode(token=token, secret_key=settings.LOCAL_JWT.LOCAL_REFRESH_TOKEN_SECRET)
        return payload

    @staticmethod
    def _handle_local_token_encode(data: dict, secret_key: str) -> str:
        encoded_jwt = jwt.encode(data, key=secret_key, algorithm=settings.LOCAL_JWT.LOCAL_JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def _handle_local_token_decode(token: str, secret_key: str) -> dict:
        try:
            payload = jwt.decode(token, key=secret_key, algorithms=[settings.LOCAL_JWT.LOCAL_JWT_ALGORITHM], )
        except JWTError:
            raise InvalidJWTException()

        return payload

    async def _handle_auth0_token_decode(self, token: str) -> dict:
        try:
            unverified_token = jws.get_unverified_header(token)
            public_key = await self._find_public_key(unverified_token["kid"])
            if public_key is None:
                raise InvalidJWTException()

            payload = jwt.decode(token=token, key=public_key, audience=settings.AUTH0_JWT.AUTH0_JWT_AUDIENCE,
                                 algorithms=settings.AUTH0_JWT.AUTH0_JWT_ALGORITHM)
            payload["auth_provider"] = AuthProviderEnum.AUTH0
        except (JWTError, JWSError, KeyError):
            raise InvalidJWTException()

        return payload

    # Later we can create a "task" that would every hour fetch keys from the endpoint
    # Or a simple variable with time or even Redis caching.
    @staticmethod
    async def _fetch_jwks() -> list[dict]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(settings.AUTH0_JWT.AUTH0_JWKS_ENDPOINT)
                response.raise_for_status()
                keys = response.json()["keys"]
                return keys
            except httpx.HTTPError:
                raise InvalidJWTException()

    async def _find_public_key(self, kid: str) -> dict | None:
        for key in await self._fetch_jwks():
            if key["kid"] == kid:
                return key
        return None

    @staticmethod
    def generate_user_id_from_auth0(auth0_sub: str) -> UUID:
        return uuid5(namespace=settings.APP.UUID_TRANSFORM_SECRET, name=auth0_sub)
