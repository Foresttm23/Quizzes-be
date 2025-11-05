import uuid

import pytest
import pytest_asyncio
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InstanceNotFoundException, RecordAlreadyExistsException, PasswordReuseException
from app.core.security import verify_password
from app.db.models.user_model import User as UserModel
from app.schemas.user_schema import SignUpRequest, UserInfoUpdateRequest, UserPasswordUpdateRequest
from app.services.user_service import UserService

pytestmark = pytest.mark.asyncio

DEFAULT_EMAIL = "test@example.com"
DEFAULT_USERNAME = "testuser"
DEFAULT_PASSWORD = SecretStr("123456789")


@pytest_asyncio.fixture
async def created_user(test_user_service: UserService) -> UserModel:
    user_info = SignUpRequest(
        email=DEFAULT_EMAIL,
        username=DEFAULT_USERNAME,
        password=DEFAULT_PASSWORD
    )
    user = await test_user_service.create_user(user_info=user_info)
    return user


async def test_create_user_success(test_user_service: UserService, testdb_session: AsyncSession):
    user_info = SignUpRequest(
        email="newuser@example.com",
        username="newuser",
        password=SecretStr("123456789")
    )
    user = await test_user_service.create_user(user_info=user_info)

    assert user.id is not None
    assert user.email == "newuser@example.com"
    assert user.username == "newuser"
    assert verify_password("123456789", user.hashed_password)

    user_in_db = await testdb_session.get(UserModel, user.id)
    assert user_in_db is not None
    assert user_in_db.email == "newuser@example.com"


async def test_create_user_duplicate_email(
        test_user_service: UserService,
        created_user: UserModel,
):
    user_info_duplicate = SignUpRequest(
        email=created_user.email,
        username="anotheruser",
        password=SecretStr("password123")
    )
    with pytest.raises(RecordAlreadyExistsException):
        await test_user_service.create_user(user_info=user_info_duplicate)


async def test_fetch_user_success(test_user_service: UserService, created_user: UserModel):
    user_from_db = await test_user_service.fetch_instance(instance_id=created_user.id)
    assert user_from_db.id == created_user.id
    assert user_from_db.email == created_user.email


async def test_fetch_user_not_found(test_user_service: UserService):
    non_existent_id = uuid.uuid4()
    with pytest.raises(InstanceNotFoundException):
        await test_user_service.fetch_instance(instance_id=non_existent_id)


# Testing both first and other pages
@pytest.mark.parametrize(
    "page, page_size, expected_has_next, expected_has_prev",
    [
        (1, 1, True, False),  # first page
        (2, 1, False, True),  # second (last) page
    ]
)
async def test_fetch_users_paginated(test_user_service: UserService, page, page_size, expected_has_next,
                                     expected_has_prev):
    user1_info = SignUpRequest(email="user1@example.com", username="user1", password=SecretStr("123456789"))
    user2_info = SignUpRequest(email="user2@example.com", username="user2", password=SecretStr("123456789"))
    await test_user_service.create_user(user1_info)
    await test_user_service.create_user(user2_info)

    paginated_users = await test_user_service.fetch_instances_paginated(page=page, page_size=page_size)

    assert paginated_users["page"] == page
    assert paginated_users["page_size"] == page_size
    assert paginated_users["has_next"] is expected_has_next
    assert paginated_users["has_prev"] is expected_has_prev

    users = paginated_users["data"]
    assert len(users) == 1
    assert users[0].email in ["user1@example.com", "user2@example.com"]


async def test_fetch_users_paginated_no_users(test_user_service: UserService):
    paginated_users = await test_user_service.fetch_instances_paginated(page=1, page_size=1)
    assert paginated_users["data"] == []


async def test_update_user_info_username(test_user_service: UserService, created_user: UserModel):
    new_user_info = UserInfoUpdateRequest(username="new_username")
    updated_user = await test_user_service.update_user_info(user_id=created_user.id, new_user_info=new_user_info)
    assert updated_user.username == "new_username"
    assert updated_user.email == created_user.email


async def test_update_user_password_success(test_user_service: UserService, created_user: UserModel):
    new_password = "new_secure_password!@#"
    new_password_info = UserPasswordUpdateRequest(
        # Since created user saves hashed_password only
        current_password=DEFAULT_PASSWORD,
        new_password=SecretStr(new_password)
    )
    original_hash = created_user.hashed_password

    updated_user = await test_user_service.update_user_password(
        user_id=created_user.id,
        new_password_info=new_password_info
    )

    assert updated_user.hashed_password != original_hash
    assert verify_password(new_password, updated_user.hashed_password)


async def test_update_user_info_no_changes(test_user_service: UserService, created_user: UserModel):
    new_user_info = UserInfoUpdateRequest()
    updated_user = await test_user_service.update_user_info(
        user_id=created_user.id,
        new_user_info=new_user_info
    )
    assert updated_user.username == created_user.username
    assert updated_user.hashed_password == created_user.hashed_password


async def test_update_user_info_not_found(test_user_service: UserService):
    non_existent_id = uuid.uuid4()
    new_user_info = UserInfoUpdateRequest(username="newuser")
    with pytest.raises(InstanceNotFoundException):
        await test_user_service.update_user_info(user_id=non_existent_id, new_user_info=new_user_info)


async def test_update_user_password_reuse_error(test_user_service: UserService, created_user: UserModel):
    new_password_info = UserPasswordUpdateRequest(
        current_password=DEFAULT_PASSWORD,
        new_password=DEFAULT_PASSWORD
    )

    with pytest.raises(PasswordReuseException):
        await test_user_service.update_user_password(
            user_id=created_user.id,
            new_password_info=new_password_info
        )


async def test_delete_user_success(test_user_service: UserService, testdb_session: AsyncSession,
                                   created_user: UserModel):
    await test_user_service.delete_instance(instance_id=created_user.id)
    user = await testdb_session.get(UserModel, created_user.id)
    assert user is None


async def test_delete_user_not_found(test_user_service: UserService):
    non_existent_id = uuid.uuid4()
    with pytest.raises(InstanceNotFoundException):
        await test_user_service.delete_instance(instance_id=non_existent_id)
