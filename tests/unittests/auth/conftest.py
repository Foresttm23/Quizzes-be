from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from pydantic import SecretStr

from auth.enums import AuthProviderEnum
from auth.models import User as UserModel
from auth.schemas import (
    JWTSchema,
    RegisterRequest,
    UserDetailsResponse,
)
from core.schemas import PaginationResponse


@pytest.fixture
def fake_timestamp():
    created_at = datetime.now(timezone.utc)
    updated_at = datetime.now(timezone.utc)
    return created_at, updated_at


@pytest.fixture
def fake_email():
    return "test@example.com"


@pytest.fixture
def fake_user_password():
    return SecretStr("curr_password")


@pytest.fixture
def fake_user_new_password():
    return SecretStr("new_password")


@pytest.fixture
def fake_user_model(fake_user):
    from company.models import Member  # noqa
    from quiz.models import QuizAttempt  # noqa

    user = UserModel(
        id=fake_user.id,
        email=fake_user.email,
        auth_provider=fake_user.auth_provider,
        hashed_password=fake_user.hashed_password,
        username=fake_user.username,
        is_banned=fake_user.is_banned,
        last_quiz_attempt_at=fake_user.last_quiz_attempt_at,
        created_at=fake_user.created_at,
        updated_at=fake_user.updated_at,
    )
    return user


@pytest.fixture
def fake_user_auth0_model(fake_user_model, fake_auth0_user):
    user = UserModel(
        id=fake_auth0_user.id,
        email=fake_auth0_user.email,
        auth_provider=fake_auth0_user.auth_provider,
        hashed_password=fake_auth0_user.hashed_password,
        username=fake_auth0_user.username,
        is_banned=fake_auth0_user.is_banned,
        last_quiz_attempt_at=fake_auth0_user.last_quiz_attempt_at,
        created_at=fake_auth0_user.created_at,
        updated_at=fake_auth0_user.updated_at,
    )
    return user


@pytest.fixture
def fake_user(fake_user_id, fake_email, fake_timestamp):
    user: UserModel = Mock(spec=UserModel)
    user.id = fake_user_id
    user.email = fake_email
    user.auth_provider = AuthProviderEnum.LOCAL
    user.hashed_password = "some_hashed_password"
    user.username = "my unique username"
    user.is_banned = False
    user.last_quiz_attempt_at = None
    user.created_at, user.updated_at = fake_timestamp
    return user


@pytest.fixture
def fake_auth0_user(fake_user, fake_timestamp):
    user: UserModel = Mock(spec=UserModel)
    user.id = fake_user.id
    user.email = fake_user.email
    user.auth_provider = AuthProviderEnum.AUTH0
    user.hashed_password = None
    user.username = f"user_{uuid4().hex}"
    user.is_banned = False
    user.last_quiz_attempt_at = None
    user.created_at, user.updated_at = fake_timestamp
    return user


@pytest.fixture
def fake_user_id():
    return uuid4()


@pytest.fixture
def fake_pagination_response(fake_user):
    fake_pagination = PaginationResponse(
        total=1,
        page=1,
        page_size=10,
        total_pages=1,
        has_next=False,
        has_prev=False,
        data=[UserDetailsResponse.model_validate(fake_user)],
    )
    return fake_pagination


@pytest.fixture
def fake_register_request(fake_user, fake_user_password):
    register_request = RegisterRequest(
        email=fake_user.email,
        username=fake_user.username,
        password=fake_user_password,
    )
    return register_request


@pytest.fixture
def fake_jwt_schema(fake_user):  # JWT is generated from the real user
    fake_schema = JWTSchema(
        sub=str(fake_user.id),
        email=fake_user.email,
        auth_provider=fake_user.auth_provider,
    )
    return fake_schema


@pytest.fixture
def mock_user_model_call(mocker, fake_user):
    mock = mocker.patch("auth.service.UserModel", return_value=fake_user)
    return mock


@pytest.fixture
def mock_auth0_user_call(mocker, fake_auth0_user):
    mock = mocker.patch("auth.service.UserModel", return_value=fake_auth0_user)
    return mock


@pytest.fixture
def mock_hash_call(mocker, fake_user):
    mock = mocker.patch(
        "auth.service.hash_password", return_value=fake_user.hashed_password
    )
    return mock


@pytest.fixture
def mock_verify_call(mocker):
    mock = mocker.patch("auth.service.verify_password", return_value=True)
    return mock


@pytest.fixture
def mock_model_hash_call(mocker, fake_user):
    mock = mocker.patch(
        "auth.models.hash_password", return_value=fake_user.hashed_password
    )
    return mock


@pytest.fixture
def mock_model_verify_call_success(mocker):
    mock = mocker.patch("auth.models.verify_password", return_value=True)
    return mock


@pytest.fixture
def mock_model_verify_call_error(mocker):
    mock = mocker.patch("auth.models.verify_password", return_value=False)
    return mock
