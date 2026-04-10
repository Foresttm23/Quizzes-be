from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr

from auth.models import User as UserModel
from auth.repository import UserRepository
from auth.schemas import (
    UserDetailsResponse,
    UserInfoUpdateRequest,
    UserPasswordUpdateRequest,
)
from auth.service import AuthService, UserService
from core.config import AppSettings
from core.exceptions import (
    ExternalAuthProviderException,
    InstanceNotFoundException,
    InvalidJWTException,
    InvalidPasswordException,
    PasswordReuseException,
    UserIncorrectPasswordOrEmailException,
)


@pytest.fixture
def mock_user_repo():
    mock = AsyncMock(spec=UserRepository)
    return mock


@pytest.fixture
def mock_user_service(mock_user_repo):
    mock = UserService(user_repo=mock_user_repo)
    return mock


@pytest.fixture
def mock_auth_service(mock_user_repo, mock_user_service, fake_uuid):
    fake_app_settings = AppSettings(UUID_TRANSFORM_SECRET=fake_uuid)
    mock = AuthService(user_service=mock_user_service, app_settings=fake_app_settings)
    return mock


@pytest.fixture
def mock_get_instance_by_field_or_none_call(mocker, mock_user_repo):
    mock = mocker.patch.object(mock_user_repo, "get_instance_by_field_or_none")
    return mock


@pytest.fixture
def mock_get_user_by_field_call(mocker, mock_user_service):
    mock = mocker.patch.object(mock_user_service, "_get_user_by_field")
    return mock


@pytest.fixture
def mock_get_user_by_field_or_none_call(mocker, mock_user_service):
    mock = mocker.patch.object(mock_user_service, "_get_user_by_field_or_none")
    return mock


@pytest.fixture
def mock_create_user_model_call(mocker, mock_user_service):
    mock = mocker.patch.object(mock_user_service, "create_user_model")
    return mock


@pytest.fixture
def mock_get_by_id_model_call(mocker, mock_user_service):
    mock = mocker.patch.object(mock_user_service, "get_by_id_model")
    return mock


@pytest.fixture
def mock_get_by_email_model_or_none_call(mocker, mock_user_service):
    mock = mocker.patch.object(mock_user_service, "get_by_email_model_or_none")
    return mock


@pytest.fixture
def mock_get_by_id_model_or_none_call(mocker, mock_user_service):
    mock = mocker.patch.object(mock_user_service, "get_by_id_model_or_none")
    return mock


@pytest.fixture
def mock_create_user_from_auth0_call(mocker, mock_user_service):
    mock = mocker.patch.object(mock_user_service, "create_user_from_auth0")
    return mock


@pytest.fixture
def mock_save_call(mocker, mock_user_repo):
    mock = mocker.patch.object(mock_user_repo, "save")
    return mock


@pytest.fixture
def mock_commit_call(mocker, mock_user_repo):
    mock = mocker.patch.object(mock_user_repo, "commit")
    return mock


@pytest.fixture
def mock_delete_instance_call(mocker, mock_user_service):
    mock = mocker.patch.object(mock_user_service, "_delete_instance")
    return mock


@pytest.fixture
def mock_get_instances_paginated_call(mocker, mock_user_repo):
    mock = mocker.patch.object(
        mock_user_repo,
        "get_instances_paginated",
    )
    return mock


@pytest.fixture
def mock_update_instance_call(mocker, mock_user_service):
    mock = mocker.patch.object(mock_user_service, "_update_instance")
    return mock


@pytest.mark.asyncio
class TestUserService:
    async def test_get_by_email_model_wiring(
        self, fake_user, fake_email, mock_get_user_by_field_call, mock_user_service
    ):
        mock_get_user_by_field_call.return_value = fake_user
        user = await mock_user_service.get_by_email_model(
            email=fake_email, relationships=None
        )

        assert user == fake_user
        mock_get_user_by_field_call.assert_awaited_once_with(
            field=UserModel.email, value=fake_email, relationships=None
        )

    async def test_get_by_email_model_or_none_wiring(
        self,
        fake_user,
        fake_email,
        mock_get_user_by_field_or_none_call,
        mock_user_service,
    ):
        mock_get_user_by_field_or_none_call.return_value = fake_user
        user = await mock_user_service.get_by_email_model_or_none(
            email=fake_email, relationships=None
        )

        assert user == fake_user
        mock_get_user_by_field_or_none_call.assert_awaited_once_with(
            field=UserModel.email, value=fake_email, relationships=None
        )

    # ------------------------------------------------------------------------------------------------------------------

    async def test_get_by_id_model_wiring(
        self, fake_user, mock_get_user_by_field_call, mock_user_service
    ):
        mock_get_user_by_field_call.return_value = fake_user
        user = await mock_user_service.get_by_id_model(
            user_id=fake_user.id, relationships=None
        )

        assert user == fake_user
        mock_get_user_by_field_call.assert_awaited_once_with(
            field=UserModel.id, value=fake_user.id, relationships=None
        )

    async def test_get_by_id_model_or_none_wiring(
        self,
        fake_user,
        fake_email,
        mock_get_user_by_field_or_none_call,
        mock_user_service,
    ):
        mock_get_user_by_field_or_none_call.return_value = fake_user
        user = await mock_user_service.get_by_id_model_or_none(
            user_id=fake_user.id, relationships=None
        )

        assert user == fake_user
        mock_get_user_by_field_or_none_call.assert_awaited_once_with(
            field=UserModel.id, value=fake_user.id, relationships=None
        )

    # ------------------------------------------------------------------------------------------------------------------
    async def test_get_by_id_wiring(
        self, fake_user, mock_get_user_by_field_call, mock_user_service
    ):
        mock_get_user_by_field_call.return_value = fake_user
        user = await mock_user_service.get_by_id(
            user_id=fake_user.id, relationships=None
        )

        assert user.id == fake_user.id
        assert isinstance(user, UserDetailsResponse)
        mock_get_user_by_field_call.assert_awaited_once_with(
            field=UserModel.id, value=fake_user.id, relationships=None
        )

    # ------------------------------------------------------------------------------------------------------------------

    @pytest.mark.parametrize("exists", [True, False])
    async def test_get_user_by_field_flow(
        self, exists, fake_user, mock_get_user_by_field_or_none_call, mock_user_service
    ):
        mock_get_user_by_field_or_none_call.return_value = fake_user if exists else None

        if not exists:
            with pytest.raises(InstanceNotFoundException):
                await mock_user_service._get_user_by_field(
                    field=UserModel.id, value=fake_user.id, relationships=None
                )

        else:
            user = await mock_user_service._get_user_by_field(
                field=UserModel.id, value=fake_user.id, relationships=None
            )
            assert user == fake_user

        mock_get_user_by_field_or_none_call.assert_awaited_once_with(
            field=UserModel.id, value=fake_user.id, relationships=None
        )

    async def test_get_users_paginated_success(
        self,
        fake_pagination_response,
        mock_get_instances_paginated_call,
        mock_user_service,
    ):
        mock_get_instances_paginated_call.return_value = fake_pagination_response
        result = await mock_user_service.get_users_paginated(
            page=fake_pagination_response.page,
            page_size=fake_pagination_response.page_size,
        )

        assert result == fake_pagination_response
        mock_get_instances_paginated_call.assert_awaited_once_with(
            page=fake_pagination_response.page,
            page_size=fake_pagination_response.page_size,
            return_schema=UserDetailsResponse,
        )

    async def test_create_user_model_success(
        self,
        mock_user_model_call,
        mock_hash_call,
        fake_user,
        fake_register_request,
        mock_save_call,
        mock_user_service,
    ):
        mock_hash_call.return_value = fake_user.hashed_password
        mock_user_model_call.return_value = fake_user

        plain_pw = fake_register_request.password.get_secret_value()
        mock_hash_call.return_value = fake_user.hashed_password

        user = await mock_user_service.create_user_model(
            user_info=fake_register_request
        )

        mock_hash_call.assert_called_once_with(password=plain_pw)
        mock_user_model_call.assert_called_once()

        mock_save_call.assert_awaited_once_with(fake_user)

        assert user == fake_user
        assert isinstance(user, UserModel)

    async def test_create_user_from_auth0_success(
        self,
        fake_auth0_user,
        mock_user_model_call,
        fake_jwt_schema,
        mock_save_call,
        mock_user_service,
    ):
        mock_user_model_call.return_value = fake_auth0_user

        user = await mock_user_service.create_user_from_auth0(
            user_id=fake_auth0_user.id, user_info=fake_jwt_schema
        )

        mock_user_model_call.assert_called_once()
        mock_save_call.assert_awaited_once_with(fake_auth0_user)
        assert user == fake_auth0_user
        assert isinstance(user, UserModel)

    async def test_update_user_info_success(
        self, fake_user, mock_save_call, mock_user_repo, mock_user_service
    ):
        mock_user_repo.apply_instance_updates.side_effect = (
            UserRepository.apply_instance_updates
        )

        new_username = "new_username"
        update_request = UserInfoUpdateRequest(username=new_username)

        await mock_user_service.update_user_info(
            user=fake_user, new_user_info=update_request
        )

        assert fake_user.username == new_username
        mock_save_call.assert_awaited_once()

    async def test_update_user_password_success(
        self,
        fake_user_model,
        mock_model_hash_call,
        mock_model_verify_call,
        mock_save_call,
        mock_user_service,
    ):
        mock_model_verify_call.return_value = True
        mock_model_hash_call.return_value = "new_hashed_string"
        request = UserPasswordUpdateRequest(
            current_password=SecretStr("old_pass"), new_password=SecretStr("new_pass")
        )

        updated_user = await mock_user_service.update_user_password(
            user=fake_user_model, new_password_info=request
        )

        assert updated_user.hashed_password == "new_hashed_string"
        mock_save_call.assert_awaited_once_with(fake_user_model)
        mock_model_verify_call.assert_awaited_once()

    @pytest.mark.parametrize(
        "is_local, current_pw, new_pw, verify_returns, expected_exception",
        [
            (True, "old_pass", "old_pass", True, PasswordReuseException),
            (True, "old_pass", "new_pass", False, InvalidPasswordException),
            (False, "old_pass", "new_pass", True, ExternalAuthProviderException),
        ],
        ids=["reuse_error", "password_error", "external_auth_error"],
    )
    async def test_update_user_password_exceptions(
        self,
        is_local,
        current_pw,
        new_pw,
        verify_returns,
        expected_exception,
        fake_user_model,
        fake_user_auth0_model,
        mock_model_verify_call,
        mock_user_service,
    ):
        user = fake_user_model if is_local else fake_user_auth0_model
        mock_model_verify_call.return_value = verify_returns
        request = UserPasswordUpdateRequest(
            current_password=SecretStr(current_pw), new_password=SecretStr(new_pw)
        )

        with pytest.raises(expected_exception):
            await mock_user_service.update_user_password(
                user=user, new_password_info=request
            )

    async def test_delete_user_success(
        self,
        fake_user_model,
        mock_commit_call,
        mock_delete_instance_call,
        mock_user_service,
    ):
        await mock_user_service.delete_user(fake_user_model)
        mock_delete_instance_call.assert_awaited_once_with(instance=fake_user_model)
        mock_commit_call.assert_awaited_once()


@pytest.mark.asyncio
class TestAuthService:
    async def test_register_user_success(
        self,
        fake_user_model,
        fake_register_request,
        mock_create_user_model_call,
        mock_auth_service,
    ):
        mock_create_user_model_call.return_value = fake_user_model

        user = await mock_auth_service.register_user(sign_up_data=fake_register_request)

        mock_create_user_model_call.assert_awaited_once_with(
            user_info=fake_register_request
        )
        assert user == fake_user_model

    @pytest.mark.parametrize("exists", [True, False])
    async def test_handle_jwt_local_flow(
        self,
        exists,
        fake_jwt_schema,
        fake_user_model,
        mock_get_by_id_model_or_none_call,
        mock_auth_service,
    ):
        mock_get_by_id_model_or_none_call.return_value = (
            fake_user_model if exists else None
        )

        if not exists:
            with pytest.raises(InvalidJWTException):
                await mock_auth_service.handle_jwt_sign_in(fake_jwt_schema)
        else:
            user = await mock_auth_service.handle_jwt_sign_in(fake_jwt_schema)
            assert user == fake_user_model

    async def test_handle_jwt_auth0_existing_user(
        self,
        fake_auth0_jwt_schema,
        fake_user_model,
        mock_get_by_id_model_or_none_call,
        mock_create_user_from_auth0_call,
        mock_auth_service,
    ):
        mock_get_by_id_model_or_none_call.return_value = fake_user_model

        user = await mock_auth_service.handle_jwt_sign_in(fake_auth0_jwt_schema)

        assert user == fake_user_model
        mock_create_user_from_auth0_call.assert_not_called()

    async def test_handle_jwt_auth0_creates_new_user(
        self,
        fake_auth0_jwt_schema,
        fake_user_model,
        mock_get_by_id_model_or_none_call,
        mock_create_user_from_auth0_call,
        mock_auth_service,
    ):
        mock_get_by_id_model_or_none_call.return_value = None
        mock_create_user_from_auth0_call.return_value = fake_user_model

        user = await mock_auth_service.handle_jwt_sign_in(fake_auth0_jwt_schema)

        assert user == fake_user_model
        mock_create_user_from_auth0_call.assert_awaited_once()

    async def test_handle_email_password_sign_in_success(
        self,
        fake_user,
        fake_login_request,
        mock_get_by_email_model_or_none_call,
        mock_verify_call,
        mock_auth_service,
    ):
        mock_get_by_email_model_or_none_call.return_value = fake_user
        mock_verify_call.return_value = True

        user = await mock_auth_service.handle_email_password_sign_in(
            sign_in_data=fake_login_request
        )

        assert user == fake_user
        mock_verify_call.assert_awaited_once()
        mock_get_by_email_model_or_none_call.assert_awaited_once_with(
            email=fake_login_request.email
        )

    @pytest.mark.parametrize(
        "exists, is_local, verify_returns, expected_exception",
        [
            [False, False, False, UserIncorrectPasswordOrEmailException],
            [True, False, False, ExternalAuthProviderException],
            [True, True, False, UserIncorrectPasswordOrEmailException],
        ],
        ids=["user_not_found", "external_provides", "wrong_pw"],
    )
    async def test_handle_email_password_sign_in_exceptions(
        self,
        exists,
        is_local,
        verify_returns,
        expected_exception,
        fake_user,
        fake_auth0_user,
        fake_login_request,
        mock_get_by_email_model_or_none_call,
        mock_verify_call,
        mock_auth_service,
    ):
        returned_user = fake_user if is_local else fake_auth0_user
        mock_get_by_email_model_or_none_call.return_value = (
            returned_user if exists else None
        )
        mock_verify_call.return_value = verify_returns

        with pytest.raises(expected_exception):
            await mock_auth_service.handle_email_password_sign_in(
                sign_in_data=fake_login_request
            )


class TestTokenService:
    pass
