from unittest.mock import Mock, AsyncMock
from uuid import uuid4

import pytest

from app.db.models.user_model import User as UserModel
from app.services.auth_service import AuthService


@pytest.fixture
def mock_user_service():
    return AsyncMock()


@pytest.fixture
def mock_auth_repository():
    return Mock()


@pytest.fixture
def auth_service(mock_user_service, mock_auth_repository, mocker):
    mocker.patch('app.services.auth_service.AuthRepository', return_value=mock_auth_repository)
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
