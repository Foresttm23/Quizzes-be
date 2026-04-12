from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr

from auth.enums import AuthProviderEnum, JWTTypeEnum
from auth.models import User as UserModel
from auth.schemas import (
    JWTRefreshSchema,
    JWTSchema,
    LoginRequest,
    RegisterRequest,
    UserDetailsResponse,
)
from core.config import AppSettings, Auth0JWTSettings, LocalJWTSettings
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
def fake_user(fake_uuid: UUID, fake_email, fake_timestamp):
    user: UserModel = Mock(spec=UserModel)
    user.id = fake_uuid
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
def fake_auth0_settings():
    settings = Auth0JWTSettings()
    return settings


@pytest.fixture
def fake_local_settings():
    settings = LocalJWTSettings()
    return settings


@pytest.fixture
def fake_app_settings(fake_uuid):
    settings = AppSettings(UUID_TRANSFORM_SECRET=fake_uuid)
    return settings


@pytest.fixture
def fake_uuid() -> UUID:
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
def fake_jwt_schema(fake_user) -> JWTSchema:  # JWT is generated from the real user
    fake_schema = JWTSchema(
        sub=str(fake_user.id),
        email=fake_user.email,
        auth_provider=fake_user.auth_provider,
    )
    return fake_schema


@pytest.fixture
def fake_jwt_refresh_schema(
    fake_user, fake_jwt_schema
) -> JWTRefreshSchema:  # JWT is generated from the real user
    fake_schema = JWTRefreshSchema(
        **fake_jwt_schema.model_dump(), type=JWTTypeEnum.REFRESH
    )
    return fake_schema


@pytest.fixture
def fake_auth0_jwt_schema(
    fake_auth0_user,
) -> JWTSchema:  # JWT is generated from the real user
    fake_schema = JWTSchema(
        sub=str(uuid4()),  # External providers have their own  ids
        email=fake_auth0_user.email,
        auth_provider=fake_auth0_user.auth_provider,
    )
    return fake_schema


@pytest.fixture
def mock_user_model_call(mocker):
    mock = mocker.patch("auth.service.UserModel")
    return mock


@pytest.fixture
def mock_hash_call(mocker):
    mock = mocker.patch("auth.service.hash_password")
    return mock


@pytest.fixture
def mock_http_client(mocker):
    # spec = HTTPClientManager
    mock = mocker.AsyncMock()
    return mock


@pytest.fixture
def mock_verify_call(mocker):
    mock = mocker.patch("auth.service.verify_password")
    return mock


@pytest.fixture
def mock_verify_local_token_and_get_payload_call(mocker):
    mock = mocker.patch("auth.service.verify_local_token_and_get_payload")
    return mock


@pytest.fixture
def mock_verify_auth0_token_and_get_payload_call(mocker):
    mock = mocker.patch("auth.service.verify_auth0_token_and_get_payload")
    return mock


@pytest.fixture
def mock_verify_refresh_token_and_get_payload_call(mocker):
    mock = mocker.patch("auth.service.verify_refresh_token_and_get_payload")
    return mock


@pytest.fixture
def mock_model_hash_call(mocker):
    mock = mocker.patch("auth.models.hash_password")
    return mock


@pytest.fixture
def mock_model_verify_call(mocker):
    mock = mocker.patch("auth.models.verify_password")
    return mock


@pytest.fixture
def mock_get_user_id_from_payload_call(mocker):
    mock = mocker.patch("auth.service.get_user_id_from_payload")
    return mock


@pytest.fixture
def mock_encode_access_token_call(mocker):
    mock = mocker.patch("auth.service.encode_access_token")
    return mock


@pytest.fixture
def mock_encode_refresh_token_call(mocker):
    mock = mocker.patch("auth.service.encode_refresh_token")
    return mock


@pytest.fixture
def fake_login_request(fake_user, fake_user_password) -> LoginRequest:
    login_request = LoginRequest(email=fake_user.email, password=fake_user_password)
    return login_request
