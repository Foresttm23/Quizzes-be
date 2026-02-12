from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid5

import httpx
import jwt
from jwt.exceptions import PyJWTError

from auth.enums import AuthProviderEnum, JWTTypeEnum
from auth.schemas import JWTSchema
from core.config import Auth0JWTSettings, LocalJWTSettings
from core.exceptions import InvalidJWTException


def encode_access_token(
    data: dict, expires_delta: timedelta, local_settings: LocalJWTSettings
) -> str:
    """Creates a signed JWT access token."""
    expire = datetime.now(timezone.utc) + expires_delta
    data.update(
        {
            "exp": expire,
            "type": JWTTypeEnum.ACCESS,
            "auth_provider": AuthProviderEnum.LOCAL,
        }
    )

    encoded_jwt = _handle_local_token_encode(
        data=data,
        secret=local_settings.LOCAL_JWT_SECRET,
        algorithm=local_settings.LOCAL_JWT_ALGORITHM,
    )
    return encoded_jwt


def encode_refresh_token(
    data: dict, expires_delta: timedelta, local_settings: LocalJWTSettings
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    data.update({"exp": expire, "type": JWTTypeEnum.REFRESH})
    encoded_jwt = _handle_local_token_encode(
        data=data,
        secret=local_settings.LOCAL_REFRESH_TOKEN_SECRET,
        algorithm=local_settings.LOCAL_JWT_ALGORITHM,
    )

    return encoded_jwt


def verify_local_token_and_get_payload(
    token: str, local_settings: LocalJWTSettings
) -> dict:
    payload = _handle_local_token_decode(
        token=token,
        secret=local_settings.LOCAL_JWT_SECRET,
        algorithm=local_settings.LOCAL_JWT_ALGORITHM,
    )
    return payload


def verify_refresh_token_and_get_payload(
    token: str, local_settings: LocalJWTSettings
) -> dict:
    payload = _handle_local_token_decode(
        token=token,
        secret=local_settings.LOCAL_REFRESH_TOKEN_SECRET,
        algorithm=local_settings.LOCAL_JWT_ALGORITHM,
    )
    return payload


async def verify_auth0_token_and_get_payload(
    token: str, auth0_settings: Auth0JWTSettings, http_client: httpx.AsyncClient
) -> dict:
    payload = await _handle_auth0_token_decode(
        token=token,
        jwks_endpoint=auth0_settings.AUTH0_JWKS_ENDPOINT,
        audience=auth0_settings.AUTH0_JWT_AUDIENCE,
        algorithm=auth0_settings.AUTH0_JWT_ALGORITHM,
        http_client=http_client,
    )
    return payload


def get_user_id_from_payload(jwt_payload: JWTSchema, uuid_secret: UUID) -> UUID:
    local = is_local_auth_provider(auth_provider=jwt_payload.auth_provider)
    if local:
        return UUID(jwt_payload.sub)

    return _generate_user_id_from_auth0(
        auth0_sub=jwt_payload.sub,
        uuid_secret=uuid_secret,
    )


def is_local_auth_provider(auth_provider: AuthProviderEnum) -> bool:
    if auth_provider != AuthProviderEnum.LOCAL:
        return False
    return True


# ----------------------------------- HELPERS -----------------------------------


def _generate_user_id_from_auth0(auth0_sub: str, uuid_secret: UUID) -> UUID:
    return uuid5(namespace=uuid_secret, name=auth0_sub)


def _handle_local_token_encode(data: dict, secret: str, algorithm: str) -> str:
    return jwt.encode(data, key=secret, algorithm=algorithm)


def _handle_local_token_decode(token: str, secret: str, algorithm: str) -> dict:
    try:
        return jwt.decode(token, key=secret, algorithms=[algorithm])
    except PyJWTError:
        raise InvalidJWTException()


async def _handle_auth0_token_decode(
    token: str,
    jwks_endpoint: str,
    audience: str,
    algorithm: str,
    http_client: httpx.AsyncClient,
) -> dict:
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise InvalidJWTException()

        public_key = await _find_public_key(
            kid=kid, jwks_endpoint=jwks_endpoint, http_client=http_client
        )
        if public_key is None:
            raise InvalidJWTException()

        payload = jwt.decode(
            token=token,
            key=public_key,
            audience=audience,
            algorithms=[algorithm],
        )
        payload["auth_provider"] = AuthProviderEnum.AUTH0
        return payload
    except PyJWTError:
        raise InvalidJWTException()


async def _fetch_jwks(jwks_endpoint: str, http_client: httpx.AsyncClient) -> list[dict]:
    try:
        response = await http_client.get(jwks_endpoint)
        response.raise_for_status()
        return response.json().get("keys", [])
    except (httpx.HTTPError, KeyError):
        raise InvalidJWTException()


async def _find_public_key(
    kid: str, jwks_endpoint: str, http_client: httpx.AsyncClient
) -> dict | None:
    keys = await _fetch_jwks(jwks_endpoint=jwks_endpoint, http_client=http_client)
    for key in keys:
        if key.get("kid") == kid:
            return key
    return None
