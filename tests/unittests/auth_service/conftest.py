from unittest.mock import Mock, AsyncMock
from uuid import uuid4

import pytest
from app.services.auth.auth_service import AuthService

from auth.models import User as UserModel


@pytest.fixture
def mock_user_service():
    return AsyncMock()


@pytest.fixture
def mock_auth_utils():
    return Mock()


@pytest.fixture
def auth_service(mock_user_service, mock_auth_utils, mocker):
    mocker.patch("src.services.auth_service.AuthUtils", return_value=mock_auth_utils)
    service = AuthService(user_service=mock_user_service)

    return service


@pytest.fixture
def mock_user():
    user = Mock(spec=UserModel)
    user.id = uuid4()
    user.email = "test@example.com"
    user.auth_provider = "local"
    user.hashed_password = "hashed_password"
    return user
