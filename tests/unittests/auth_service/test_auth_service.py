from datetime import timedelta
from unittest.mock import Mock

import pytest
from app.core.exceptions import (
    InvalidJWTException,
    InstanceNotFoundException,
    UserIncorrectPasswordOrEmailException,
)
from app.schemas.user.user_request_schema import LoginRequest


def test_verify_token_and_get_payload_local_success(auth_service, mock_auth_utils):
    mock_payload = {"id": "123", "email": "test@local.com"}
    mock_auth_utils.verify_local_token_and_get_payload.return_value = mock_payload

    result = auth_service.verify_token_and_get_payload("valid_local_token")

    assert result == mock_payload
    mock_auth_utils.verify_auth0_token_and_get_payload.assert_not_called()


def test_verify_token_and_get_payload_auth0_fallback_success(
    auth_service, mock_auth_utils
):
    mock_payload = {"email": "test@auth0.com"}
    mock_auth_utils.verify_local_token_and_get_payload.side_effect = InvalidJWTException
    mock_auth_utils.verify_auth0_token_and_get_payload.return_value = mock_payload

    result = auth_service.verify_token_and_get_payload("valid_auth0_token")

    assert result == mock_payload
    mock_auth_utils.verify_local_token_and_get_payload.assert_called_once()
    mock_auth_utils.verify_auth0_token_and_get_payload.assert_called_once()


def test_verify_token_and_get_payload_all_fail(auth_service, mock_auth_utils):
    mock_auth_utils.verify_local_token_and_get_payload.side_effect = InvalidJWTException
    mock_auth_utils.verify_auth0_token_and_get_payload.side_effect = InvalidJWTException

    with pytest.raises(InvalidJWTException):
        auth_service.verify_token_and_get_payload("invalid_token")


@pytest.mark.asyncio
async def test_handle_jwt_sign_in_user_exists(
    auth_service, mock_user_service, mock_user
):
    jwt_payload = {"email": mock_user.email}
    mock_user_service.fetch_user.return_value = mock_user

    user = await auth_service.handle_jwt_sign_in(jwt_payload)

    assert user == mock_user
    mock_user_service.fetch_user.assert_called_once_with(
        field="email", value=mock_user.email
    )
    mock_user_service.create_user_from_auth0.assert_not_called()


@pytest.mark.asyncio
async def test_handle_jwt_sign_in_user_not_found(
    auth_service, mock_user_service, mock_user
):
    jwt_payload = {"email": "new@auth0.com"}
    mock_user_service.fetch_user.side_effect = InstanceNotFoundException
    mock_user_service.create_user_from_auth0.return_value = mock_user

    user = await auth_service.handle_jwt_sign_in(jwt_payload)

    assert user == mock_user
    mock_user_service.fetch_user.assert_called_once_with(
        field="email", value=jwt_payload["email"]
    )
    mock_user_service.create_user_from_auth0.assert_called_once_with(
        user_info=jwt_payload
    )


def test_create_access_token_calls_repo_correctly(
    mocker, auth_service, mock_user, mock_auth_utils
):
    mock_settings = mocker.patch("src.services.auth_service.settings")
    mock_settings.LOCAL_JWT.LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES = 60

    mock_auth_utils.create_access_token.return_value = "signed_jwt_token"

    expected_data = mock_auth_utils.fill_jwt_fields_from_dict(data=mock_user.to_dict())
    expected_expires_delta = timedelta(minutes=60)

    token = auth_service._create_access_token(mock_user)

    assert token == "signed_jwt_token"
    mock_auth_utils.create_access_token.assert_called_once_with(
        data=expected_data, expires_delta=expected_expires_delta
    )


@pytest.mark.asyncio
async def test_handle_email_password_sign_in_success(
    mocker, auth_service, mock_user, mock_user_service
):
    mock_verify_password = mocker.patch("src.services.auth_service.verify_password")

    sign_in_data = Mock(spec=LoginRequest)
    sign_in_data.email = mock_user.email

    mock_secret_str = Mock()
    mock_secret_str.get_secret_value.return_value = "correct_password"
    sign_in_data.password = mock_secret_str

    mock_user_service.fetch_user.return_value = mock_user
    mock_verify_password.return_value = True

    user = await auth_service.handle_email_password_sign_in(sign_in_data)

    assert user == mock_user
    mock_user_service.fetch_user.assert_called_once_with(
        field="email", value=mock_user.email
    )
    mock_verify_password.assert_called_once_with(
        "correct_password", mock_user.hashed_password
    )


@pytest.mark.asyncio
async def test_handle_email_password_sign_in_user_not_found(
    auth_service, mock_user_service, mock_user
):
    sign_in_data = Mock(spec=LoginRequest)
    sign_in_data.email = mock_user.email

    mock_user_service.fetch_user.side_effect = InstanceNotFoundException

    with pytest.raises(UserIncorrectPasswordOrEmailException):
        await auth_service.handle_email_password_sign_in(sign_in_data)

    mock_user_service.fetch_user.assert_called_once()


@pytest.mark.asyncio
async def test_handle_email_password_sign_in_incorrect_password(
    mocker, auth_service, mock_user, mock_user_service
):
    mock_verify_password = mocker.patch("src.services.auth_service.verify_password")

    sign_in_data = Mock(spec=LoginRequest)
    sign_in_data.email = mock_user.email

    mock_secret_str = Mock()
    mock_secret_str.get_secret_value.return_value = "wrong_password"
    sign_in_data.password = mock_secret_str

    mock_user_service.fetch_user.return_value = mock_user
    mock_verify_password.return_value = False

    with pytest.raises(UserIncorrectPasswordOrEmailException):
        await auth_service.handle_email_password_sign_in(sign_in_data)

    mock_verify_password.assert_called_once()
