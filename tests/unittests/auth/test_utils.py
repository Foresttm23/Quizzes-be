from datetime import timedelta
from uuid import uuid4

import httpx
import jwt
import pytest
from jwt import PyJWTError

from auth.enums import AuthProviderEnum
from auth.utils import (
    _fetch_jwks,
    _find_public_key,
    _handle_auth0_token_decode,
    _handle_local_token_decode,
    _handle_local_token_encode,
    encode_access_token,
    encode_refresh_token,
    get_user_id_from_payload,
    is_local_auth_provider,
    verify_auth0_token_and_get_payload,
    verify_local_token_and_get_payload,
    verify_refresh_token_and_get_payload,
)
from core.exceptions import InvalidJWTException


@pytest.fixture
def mock_fetch_jwks_call(mocker):
    mock = mocker.patch("auth.utils._fetch_jwks")
    return mock


@pytest.fixture
def mock_get_unverified_header_call(mocker):
    mock = mocker.patch("jwt.get_unverified_header")
    return mock


@pytest.fixture
def mock_find_public_key_call(mocker):
    mock = mocker.patch("auth.utils._find_public_key")
    return mock


@pytest.fixture
def mock_handle_local_token_encode_call(mocker):
    mock = mocker.patch("auth.utils._handle_local_token_encode")
    return mock


@pytest.fixture
def mock_handle_local_token_decode_call(mocker):
    mock = mocker.patch("auth.utils._handle_local_token_decode")
    return mock


@pytest.fixture
def mock_handle_auth0_token_decode_call(mocker):
    mock = mocker.patch("auth.utils._handle_auth0_token_decode")
    return mock


@pytest.fixture
def mock_generate_user_id_from_auth0_call(mocker):
    mock = mocker.patch("auth.utils._generate_user_id_from_auth0")
    return mock


@pytest.fixture
def mock_jwt_encode_call(mocker):
    mock = mocker.patch("jwt.encode")
    return mock


@pytest.fixture
def mock_jwt_decode_call(mocker):
    mock = mocker.patch("jwt.decode")
    return mock


def test_encode_access_token(
    fake_local_settings, fake_jwt_schema, mock_handle_local_token_encode_call
) -> None:
    data = fake_jwt_schema.model_dump()
    expires_delta = timedelta(seconds=1)

    expected_token = "token"
    mock_handle_local_token_encode_call.return_value = expected_token

    encoded_jwt = encode_access_token(
        data=data, expires_delta=expires_delta, local_settings=fake_local_settings
    )

    assert encoded_jwt == expected_token
    mock_handle_local_token_encode_call.assert_called_once_with(
        data=data,
        secret=fake_local_settings.LOCAL_JWT_SECRET,
        algorithm=fake_local_settings.LOCAL_JWT_ALGORITHM,
    )


def test_encode_refresh_token(
    fake_local_settings, fake_jwt_schema, mock_handle_local_token_encode_call
):
    data = fake_jwt_schema.model_dump()
    expires_delta = timedelta(seconds=1)

    expected_token = "token"
    mock_handle_local_token_encode_call.return_value = expected_token

    encoded_jwt = encode_refresh_token(
        data=data, expires_delta=expires_delta, local_settings=fake_local_settings
    )

    assert encoded_jwt == expected_token
    mock_handle_local_token_encode_call.assert_called_once_with(
        data=data,
        secret=fake_local_settings.LOCAL_REFRESH_TOKEN_SECRET,
        algorithm=fake_local_settings.LOCAL_JWT_ALGORITHM,
    )


def test_verify_local_token_and_get_payload(
    fake_local_settings, mock_handle_local_token_decode_call
):
    fake_token = "token"
    expected_payload = {1: "payload"}

    mock_handle_local_token_decode_call.return_value = expected_payload

    payload = verify_local_token_and_get_payload(
        token=fake_token, local_settings=fake_local_settings
    )

    assert payload == expected_payload
    mock_handle_local_token_decode_call.assert_called_once_with(
        token=fake_token,
        secret=fake_local_settings.LOCAL_JWT_SECRET,
        algorithm=fake_local_settings.LOCAL_JWT_ALGORITHM,
    )


def test_verify_refresh_token_and_get_payload(
    fake_local_settings, mock_handle_local_token_decode_call
):
    fake_token = "token"
    expected_payload = {1: "payload"}

    mock_handle_local_token_decode_call.return_value = expected_payload

    payload = verify_refresh_token_and_get_payload(
        token=fake_token, local_settings=fake_local_settings
    )

    assert payload == expected_payload
    mock_handle_local_token_decode_call.assert_called_once_with(
        token=fake_token,
        secret=fake_local_settings.LOCAL_REFRESH_TOKEN_SECRET,
        algorithm=fake_local_settings.LOCAL_JWT_ALGORITHM,
    )


@pytest.mark.asyncio
async def test_verify_auth0_token_and_get_payload(
    fake_auth0_settings, mock_handle_auth0_token_decode_call, mock_http_client
):
    fake_token = "token"
    expected_payload = {1: "payload"}

    mock_handle_auth0_token_decode_call.return_value = expected_payload

    payload = await verify_auth0_token_and_get_payload(
        token=fake_token,
        auth0_settings=fake_auth0_settings,
        http_client=mock_http_client,
    )

    assert payload == expected_payload
    mock_handle_auth0_token_decode_call.assert_called_once_with(
        token=fake_token,
        jwks_endpoint=fake_auth0_settings.AUTH0_JWKS_ENDPOINT,
        audience=fake_auth0_settings.AUTH0_JWT_AUDIENCE,
        algorithm=fake_auth0_settings.AUTH0_JWT_ALGORITHM,
        http_client=mock_http_client,
    )


def test_get_user_id_from_payload_local(fake_jwt_schema, fake_uuid):
    user_id = get_user_id_from_payload(fake_jwt_schema, uuid_secret=fake_uuid)
    assert user_id == fake_uuid


def test_get_user_id_from_payload_auth0(
    fake_auth0_jwt_schema, mock_generate_user_id_from_auth0_call, fake_uuid
):
    mock_generate_user_id_from_auth0_call.return_value = fake_uuid

    dummy_secret = uuid4()
    user_id = get_user_id_from_payload(
        jwt_payload=fake_auth0_jwt_schema, uuid_secret=dummy_secret
    )

    assert user_id == fake_uuid
    mock_generate_user_id_from_auth0_call.assert_called_once_with(
        auth0_sub=fake_auth0_jwt_schema.sub, uuid_secret=dummy_secret
    )


@pytest.mark.parametrize(
    "provider, expected",
    [
        (AuthProviderEnum.LOCAL, True),
        (AuthProviderEnum.AUTH0, False),
    ],
)
def test_is_local_auth_provider(provider, expected):
    """Ensures the local provider check identifies LOCAL correctly."""
    assert is_local_auth_provider(provider) is expected


# ----------------------------------- HELPERS -----------------------------------


def test_handle_local_token_encode(fake_local_settings, mock_jwt_encode_call):
    expected_value = "encoded_token"
    mock_jwt_encode_call.return_value = expected_value

    payload = {"sub": "user_123"}

    encoded_token = _handle_local_token_encode(
        data=payload,
        secret=fake_local_settings.LOCAL_JWT_SECRET,
        algorithm=fake_local_settings.LOCAL_JWT_ALGORITHM,
    )

    assert encoded_token == expected_value
    mock_jwt_encode_call.assert_called_once_with(
        payload,
        key=fake_local_settings.LOCAL_JWT_SECRET,
        algorithm=fake_local_settings.LOCAL_JWT_ALGORITHM,
    )


def test_handle_local_token_decode_success(mock_jwt_decode_call, fake_local_settings):
    token = "token"
    expected_value = {"sub": "user_123"}
    mock_jwt_decode_call.return_value = expected_value

    result = _handle_local_token_decode(
        token=token,
        secret=fake_local_settings.LOCAL_JWT_SECRET,
        algorithm=fake_local_settings.LOCAL_JWT_ALGORITHM,
    )

    assert result == expected_value
    mock_jwt_decode_call.assert_called_once_with(
        jwt=token,
        key=fake_local_settings.LOCAL_JWT_SECRET,
        algorithms=[fake_local_settings.LOCAL_JWT_ALGORITHM],
    )


def test_handle_local_token_decode_failure(mock_jwt_decode_call, fake_local_settings):
    mock_jwt_decode_call.side_effect = PyJWTError

    with pytest.raises(InvalidJWTException):
        _handle_local_token_decode(
            token="token",
            secret=fake_local_settings.LOCAL_JWT_SECRET,
            algorithm=fake_local_settings.LOCAL_JWT_ALGORITHM,
        )


@pytest.mark.asyncio
async def test_fetch_jwks_success(mocker, mock_http_client):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"keys": [{"kid": "123", "use": "sig"}]}
    mock_response.raise_for_status = mocker.Mock()

    mock_http_client.get.return_value = mock_response

    keys = await _fetch_jwks("https://example.com/jwks", mock_http_client)

    assert len(keys) == 1
    assert keys[0]["kid"] == "123"
    mock_http_client.get.assert_called_once_with("https://example.com/jwks")
    mock_response.raise_for_status.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_jwks_http_error(mock_http_client):
    mock_http_client.get.side_effect = httpx.HTTPError("Connection failed")

    with pytest.raises(InvalidJWTException):
        await _fetch_jwks("https://example.com/jwks", mock_http_client)


@pytest.mark.asyncio
async def test_fetch_jwks_status_code_error(mocker, mock_http_client):
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=mocker.Mock(), response=mock_response
    )
    mock_http_client.get.return_value = mock_response

    with pytest.raises(InvalidJWTException):
        await _fetch_jwks("https://example.com/jwks", mock_http_client)


@pytest.mark.asyncio
async def test_find_public_key_success(mock_fetch_jwks_call, mock_http_client):
    target_key = {"kid": "match", "n": "..."}
    mock_keys = [{"kid": "other", "n": "..."}, target_key]

    mock_fetch_jwks_call.return_value = mock_keys

    result = await _find_public_key(
        kid="match", jwks_endpoint="url", http_client=mock_http_client
    )

    assert result == target_key


@pytest.mark.asyncio
async def test_find_public_key_not_found(mock_fetch_jwks_call, mock_http_client):
    mock_keys = [{"kid": "other"}]

    mock_fetch_jwks_call.return_value = mock_keys

    result = await _find_public_key(
        kid="missing", jwks_endpoint="url", http_client=mock_http_client
    )

    assert result is None


@pytest.mark.asyncio
async def test_handle_auth0_token_decode_success(
    mock_http_client,
    mock_get_unverified_header_call,
    mock_find_public_key_call,
    mock_jwt_decode_call,
):
    mock_get_unverified_header_call.return_value = {"kid": "key_123"}

    mock_key = {"kid": "key_123", "n": "..."}
    mock_find_public_key_call.return_value = mock_key

    expected_payload = {"sub": "auth0|user1"}
    mock_jwt_decode_call.return_value = expected_payload.copy()

    result = await _handle_auth0_token_decode(
        token="valid.token.here",
        jwks_endpoint="https://auth0.com/.well-known/jwks.json",
        audience="my-api",
        algorithm="RS256",
        http_client=mock_http_client,
    )

    assert result["sub"] == "auth0|user1"
    assert result["auth_provider"] == AuthProviderEnum.AUTH0
    jwt.decode.assert_called_once()


@pytest.mark.asyncio
async def test_handle_auth0_token_decode_no_kid(
    mock_get_unverified_header_call, mock_http_client
):
    mock_get_unverified_header_call.return_value = {}

    with pytest.raises(InvalidJWTException):
        await _handle_auth0_token_decode(
            "token", "url", "aud", "RS256", mock_http_client
        )


@pytest.mark.asyncio
async def test_handle_auth0_token_decode_key_not_found(
    mock_get_unverified_header_call, mock_find_public_key_call, mock_http_client
):
    mock_get_unverified_header_call.return_value = {"kid": "missing"}
    mock_find_public_key_call.return_value = None

    with pytest.raises(InvalidJWTException):
        await _handle_auth0_token_decode(
            "token", "url", "aud", "RS256", mock_http_client
        )


@pytest.mark.asyncio
async def test_handle_auth0_token_decode_jwt_error(
    mock_get_unverified_header_call,
    mock_find_public_key_call,
    mock_jwt_decode_call,
    mock_http_client,
):
    mock_get_unverified_header_call.return_value = {"kid": "123"}
    mock_find_public_key_call.return_value = {"kid": "123"}

    mock_jwt_decode_call.side_effect = PyJWTError

    with pytest.raises(InvalidJWTException):
        await _handle_auth0_token_decode(
            "token", "url", "aud", "RS256", mock_http_client
        )
