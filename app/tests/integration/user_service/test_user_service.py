import pytest
from app.schemas.user_schemas.user_request_schema import RegisterRequest, UserInfoUpdateRequest, \
    UserPasswordUpdateRequest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InstanceNotFoundException, RecordAlreadyExistsException, PasswordReuseException
from app.utils.password_utils import verify_password
from db.models.user.user_model import User as UserModel
from services.user.user_service import UserService

pytestmark = pytest.mark.asyncio

DEFAULT_EMAIL = "test@example.com"
DEFAULT_USERNAME = "testuser"
DEFAULT_PASSWORD = SecretStr("123456789")


async def test_create_user_success(test_user_service: UserService):
    user_info = RegisterRequest(email=DEFAULT_EMAIL, username=DEFAULT_USERNAME, password=DEFAULT_PASSWORD)
    user = await test_user_service.create_user(user_info=user_info)

    assert user.id is not None
    assert user.email == DEFAULT_EMAIL
    assert user.username == DEFAULT_USERNAME
    assert verify_password("123456789", user.hashed_password)


async def test_create_user_duplicate_email(test_user_service: UserService, created_user: UserModel):
    user_info_duplicate = RegisterRequest(email=created_user.email, username=DEFAULT_USERNAME,
                                          password=DEFAULT_PASSWORD)
    with pytest.raises(RecordAlreadyExistsException):
        await test_user_service.create_user(user_info=user_info_duplicate)


async def test_create_user_from_jwt(test_user_service: UserService):
    user_info = {"email": DEFAULT_EMAIL}
    user = await test_user_service.create_user_from_auth0(user_info=user_info)

    assert isinstance(user, UserModel)
    assert user.email == DEFAULT_EMAIL
    assert user.hashed_password is None
    assert user.auth_provider == "auth0"
    assert user.username.startswith("user_")


async def test_update_user_info_username(test_user_service: UserService, created_user: UserModel):
    new_user_info = UserInfoUpdateRequest(username="new_username")
    updated_user = await test_user_service.update_user_info(user=created_user, new_user_info=new_user_info)
    assert updated_user.username == "new_username"
    assert updated_user.email == created_user.email


async def test_update_user_password_success(test_user_service: UserService, created_user: UserModel):
    new_password = "new_secure_password!@#"
    new_password_info = UserPasswordUpdateRequest(  # Since created user saves hashed_password only
        current_password=DEFAULT_PASSWORD, new_password=SecretStr(new_password))
    original_hash = created_user.hashed_password

    updated_user = await test_user_service.update_user_password(user=created_user, new_password_info=new_password_info)

    assert updated_user.hashed_password != original_hash
    assert verify_password(new_password, updated_user.hashed_password)


async def test_update_user_info_no_changes(test_user_service: UserService, created_user: UserModel):
    new_user_info = UserInfoUpdateRequest(username=created_user.username)
    updated_user = await test_user_service.update_user_info(user=created_user, new_user_info=new_user_info)
    assert updated_user.username == created_user.username
    assert updated_user.hashed_password == created_user.hashed_password


async def test_update_user_password_reuse_error(test_user_service: UserService, created_user: UserModel):
    new_password_info = UserPasswordUpdateRequest(current_password=DEFAULT_PASSWORD, new_password=DEFAULT_PASSWORD)

    with pytest.raises(PasswordReuseException):
        await test_user_service.update_user_password(user=created_user, new_password_info=new_password_info)


# ------------------------------------PRETTY MUCH OBSOLETE, SINCE BASE SERVICE ALREADY TESTS THIS------------------------------------

async def test_fetch_user_success(test_user_service: UserService, created_user: UserModel):
    user_from_db = await test_user_service.get_by_id(user_id=created_user.id)
    assert user_from_db.id == created_user.id
    assert user_from_db.email == created_user.email


async def test_fetch_user_not_found(test_user_service: UserService):
    non_existent_email = "Some wrong user email"
    with pytest.raises(InstanceNotFoundException):
        await test_user_service.get_by_email(email=non_existent_email)


# Testing both first and other pages
@pytest.mark.parametrize("page, page_size, expected_has_next, expected_has_prev", [(1, 1, True, False),  # first page
                                                                                   (2, 1, False, True),
                                                                                   # second (last) page
                                                                                   ])
async def test_fetch_users_paginated(test_user_service: UserService, page, page_size, expected_has_next,
                                     expected_has_prev):
    user1_info = RegisterRequest(email="1" + DEFAULT_EMAIL, username="1" + DEFAULT_USERNAME, password=DEFAULT_PASSWORD)
    user2_info = RegisterRequest(email="2" + DEFAULT_EMAIL, username="2" + DEFAULT_USERNAME, password=DEFAULT_PASSWORD)
    await test_user_service.create_user(user1_info)
    await test_user_service.create_user(user2_info)

    paginated_users = await test_user_service.get_users_paginated(page=page, page_size=page_size)

    assert paginated_users["page"] == page
    assert paginated_users["page_size"] == page_size
    assert paginated_users["has_next"] is expected_has_next
    assert paginated_users["has_prev"] is expected_has_prev

    users = paginated_users["data"]
    assert len(users) == 1
    assert users[0].email in ["1" + DEFAULT_EMAIL, "2" + DEFAULT_EMAIL]


async def test_fetch_users_paginated_no_users(test_user_service: UserService):
    paginated_users = await test_user_service.get_users_paginated(page=1, page_size=1)
    assert paginated_users["data"] == []


async def test_delete_user_success(test_user_service: UserService, testdb_session: AsyncSession,
                                   created_user: UserModel):
    await test_user_service.delete_user(user=created_user)
    user = await testdb_session.get(UserModel, created_user.id)
    assert user is None
