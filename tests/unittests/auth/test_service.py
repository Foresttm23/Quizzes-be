from typing import cast
from unittest.mock import ANY, AsyncMock

import pytest
from pydantic import SecretStr

from auth.models import User as UserModel
from auth.repository import UserRepository
from auth.schemas import (
    UserDetailsResponse,
    UserInfoUpdateRequest,
    UserPasswordUpdateRequest,
)
from auth.service import UserService
from core.exceptions import (
    ExternalAuthProviderException,
    InstanceNotFoundException,
    InvalidPasswordException,
    PasswordReuseException,
)


@pytest.mark.asyncio
class TestUserService:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock_repo: UserRepository = AsyncMock(spec=UserRepository)
        self.service: UserService = UserService(user_repo=self.mock_repo)

    @pytest.fixture
    def mock_save_call(self):
        mock = cast(AsyncMock, self.mock_repo.save)
        return mock

    @pytest.fixture
    def mock_commit_call(self):
        mock = cast(AsyncMock, self.mock_repo.commit)
        return mock

    @pytest.fixture
    def mock_delete_instance_call(self, mocker):
        mock = mocker.patch.object(self.service, "_delete_instance")
        return mock

    async def _assert_instance_not_found(self, coro_func):
        self.mock_repo.get_instance_by_field_or_none.return_value = None
        with pytest.raises(InstanceNotFoundException):
            await coro_func

    # ------------------------------------------------------------------------------------------------------------------

    async def test_get_by_email_model_success(self, fake_user, fake_email):
        self.mock_repo.get_instance_by_field_or_none = AsyncMock(return_value=fake_user)

        result = await self.service.get_by_email_model(
            email=fake_email, relationships=None
        )

        assert result == fake_user

        self.mock_repo.get_instance_by_field_or_none.assert_awaited_once_with(
            field=UserModel.email, value=fake_email, relationships=None
        )

    async def test_get_by_email_model_error(self, fake_user, fake_email):
        await self._assert_instance_not_found(
            self.service.get_by_email_model(email=fake_email, relationships=None)
        )

    # ------------------------------------------------------------------------------------------------------------------

    async def test_get_by_id_model_success(self, fake_user, fake_user_id):
        self.mock_repo.get_instance_by_field_or_none = AsyncMock(return_value=fake_user)

        result = await self.service.get_by_id_model(
            user_id=fake_user_id, relationships=None
        )

        assert result == fake_user

        self.mock_repo.get_instance_by_field_or_none.assert_awaited_once_with(
            field=UserModel.id, value=fake_user_id, relationships=None
        )

    async def test_get_by_id_model_error(self, fake_user, fake_user_id):
        await self._assert_instance_not_found(
            self.service.get_by_id_model(user_id=fake_user_id, relationships=None)
        )

    # ------------------------------------------------------------------------------------------------------------------

    async def test_get_by_id_success(self, fake_user, fake_user_id):
        self.mock_repo.get_instance_by_field_or_none = AsyncMock(return_value=fake_user)

        result = await self.service.get_by_id(user_id=fake_user_id, relationships=None)

        assert isinstance(result, UserDetailsResponse)

        self.mock_repo.get_instance_by_field_or_none.assert_awaited_once_with(
            field=UserModel.id, value=fake_user_id, relationships=None
        )

    async def test_get_by_id_error(self, fake_user, fake_user_id):
        await self._assert_instance_not_found(
            self.service.get_by_id(user_id=fake_user_id, relationships=None)
        )

    # ------------------------------------------------------------------------------------------------------------------

    async def test_get_users_paginated_success(self, fake_pagination_response):
        self.mock_repo.get_instances_paginated = AsyncMock(
            return_value=fake_pagination_response
        )

        result = await self.service.get_users_paginated(
            page=fake_pagination_response.page,
            page_size=fake_pagination_response.page_size,
        )

        assert result == fake_pagination_response
        self.mock_repo.get_instances_paginated.assert_awaited_once_with(
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
    ):
        plain_pw = fake_register_request.password.get_secret_value()
        mock_hash_call.return_value = fake_user.hashed_password

        user = await self.service.create_user_model(user_info=fake_register_request)

        mock_hash_call.assert_called_once_with(password=plain_pw)
        mock_user_model_call.assert_called_once()

        mock_save_call.assert_awaited_once_with(fake_user)

        assert user == fake_user
        assert isinstance(user, UserModel)

    async def test_create_user_from_auth0_success(
        self, fake_auth0_user, mock_auth0_user_call, fake_jwt_schema, mock_save_call
    ):
        user = await self.service.create_user_from_auth0(
            user_id=fake_auth0_user.id, user_info=fake_jwt_schema
        )

        mock_auth0_user_call.assert_called_once()
        mock_save_call.assert_awaited_once_with(fake_auth0_user)
        assert user == fake_auth0_user
        assert isinstance(user, UserModel)

    async def test_update_user_info_success(
        self, fake_user, mock_user_model_call, mock_save_call
    ):
        """
        Tests that the user gets updated correctly with the provided info.
        Since the UserRepository.apply_instance_updates method doesn't use the db connection, we use the real method for testing.
        """
        # Run real method, since it updates fields using python getattr and setattr.
        # If db connection is used, we should fake the return value
        self.mock_repo.apply_instance_updates = UserRepository.apply_instance_updates

        new_username = "new_username"
        update_request = UserInfoUpdateRequest(username=new_username)

        updated_user = await self.service.update_user_info(
            user=fake_user, new_user_info=update_request
        )

        assert updated_user.username == new_username
        mock_save_call.assert_awaited_once_with(fake_user)

    async def test_update_user_password_success(
        self,
        mock_save_call,
        fake_user_model,
        mock_model_hash_call,
        mock_model_verify_call_success,
    ):
        current_plain_pw = "old_passw"
        new_plain_pw = "new_passw"
        user_password_update_request = UserPasswordUpdateRequest(
            current_password=SecretStr(current_plain_pw),
            new_password=SecretStr(new_plain_pw),
        )

        updated_user = await self.service.update_user_password(
            user=fake_user_model, new_password_info=user_password_update_request
        )

        assert updated_user.hashed_password == mock_model_hash_call.return_value
        mock_save_call.assert_awaited_once_with(fake_user_model)
        mock_model_verify_call_success.assert_awaited_once_with(
            plain_password=current_plain_pw, hashed_password=ANY
        )
        mock_model_hash_call.assert_awaited_once_with(password=new_plain_pw)

    async def test_update_user_password_error_same_password(
        self,
        fake_user_model,
    ):
        old_plain_pw = "old_passw"
        user_password_update_request = UserPasswordUpdateRequest(
            current_password=SecretStr(old_plain_pw),
            new_password=SecretStr(old_plain_pw),
        )

        with pytest.raises(PasswordReuseException):
            await self.service.update_user_password(
                user=fake_user_model, new_password_info=user_password_update_request
            )

    async def test_update_user_password_error_hashed_password_is_none(
        self,
        fake_user_auth0_model,
    ):
        user_password_update_request = UserPasswordUpdateRequest(
            current_password=SecretStr("old_passw"), new_password=SecretStr("new_passw")
        )

        with pytest.raises(ExternalAuthProviderException):
            await self.service.update_user_password(
                user=fake_user_auth0_model,
                new_password_info=user_password_update_request,
            )

    async def test_update_user_password_error_verify_password_is_false(
        self, fake_user_model, mock_model_verify_call_error
    ):
        invalid_old_pw = "invalid_old_pw"
        user_password_update_request = UserPasswordUpdateRequest(
            current_password=SecretStr(invalid_old_pw),
            new_password=SecretStr("new_passw"),
        )

        with pytest.raises(InvalidPasswordException):
            await self.service.update_user_password(
                user=fake_user_model,
                new_password_info=user_password_update_request,
            )

    async def test_delete_user_success(
        self, fake_user_model, mock_commit_call, mock_delete_instance_call
    ):
        await self.service.delete_user(fake_user_model)
        mock_delete_instance_call.assert_awaited_once_with(instance=fake_user_model)
        mock_commit_call.assert_awaited_once()
