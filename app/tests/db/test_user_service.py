import uuid

import pytest
import pytest_asyncio
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InstanceNotFoundException, RecordAlreadyExistsException, PasswordReuseException
from app.core.security import verify_password
from app.db.models.user import User as UserModel
from app.schemas.user_schema import SignUpRequest, UserInfoUpdateRequest, UserPasswordUpdateRequest
from app.services.user_service import (
    create_user_service,
    get_user_service,
    get_users_service,
    update_user_info_service,
    delete_user_service, update_user_password_service
)

pytestmark = pytest.mark.asyncio

DEFAULT_EMAIL = "test@example.com"
DEFAULT_USERNAME = "testuser"
DEFAULT_PASSWORD = SecretStr("123456789")


@pytest_asyncio.fixture
async def created_user(testdb_session: AsyncSession) -> UserModel:
    user_info = SignUpRequest(
        email=DEFAULT_EMAIL,
        username=DEFAULT_USERNAME,
        password=DEFAULT_PASSWORD
    )
    user = await create_user_service(user_info=user_info, db=testdb_session)
    return user


async def test_create_user_service_success(testdb_session: AsyncSession):
    user_info = SignUpRequest(
        email="newuser@example.com",
        username="newuser",
        password=SecretStr("123456789")
    )
    user = await create_user_service(user_info=user_info, db=testdb_session)

    assert user.id is not None
    assert user.email == "newuser@example.com"
    assert user.username == "newuser"
    assert verify_password("123456789", user.hashed_password)

    user_in_db = await testdb_session.get(UserModel, user.id)
    assert user_in_db is not None
    assert user_in_db.email == "newuser@example.com"


async def test_create_user_service_duplicate_email(
        testdb_session: AsyncSession,
        created_user: UserModel,
):
    user_info_duplicate = SignUpRequest(
        email=created_user.email,
        username="anotheruser",
        password=SecretStr("password123")
    )
    with pytest.raises(RecordAlreadyExistsException):
        await create_user_service(user_info=user_info_duplicate, db=testdb_session)


async def test_get_user_service_success(testdb_session: AsyncSession, created_user: UserModel):
    user_from_db = await get_user_service(user_id=created_user.id, db=testdb_session)
    assert user_from_db.id == created_user.id
    assert user_from_db.email == created_user.email


async def test_get_user_service_not_found(testdb_session: AsyncSession):
    non_existent_id = uuid.uuid4()
    with pytest.raises(InstanceNotFoundException):
        await get_user_service(user_id=non_existent_id, db=testdb_session)


# Testing both first and other pages
@pytest.mark.parametrize(
    "page, page_size, expected_has_next, expected_has_prev",
    [
        (1, 1, True, False),  # first page
        (2, 1, False, True),  # second (last) page
    ]
)
async def test_get_users_service_pagination(testdb_session, page, page_size, expected_has_next, expected_has_prev):
    user1_info = SignUpRequest(email="user1@example.com", username="user1", password=SecretStr("123456789"))
    user2_info = SignUpRequest(email="user2@example.com", username="user2", password=SecretStr("123456789"))
    await create_user_service(user1_info, db=testdb_session)
    await create_user_service(user2_info, db=testdb_session)

    paginated_users = await get_users_service(page=page, page_size=page_size, db=testdb_session)

    assert paginated_users["page"] == page
    assert paginated_users["page_size"] == page_size
    assert paginated_users["has_next"] is expected_has_next
    assert paginated_users["has_prev"] is expected_has_prev

    users = paginated_users["data"]
    assert len(users) == 1
    assert users[0].email in ["user1@example.com", "user2@example.com"]


async def test_get_users_service_with_pagination_no_users(testdb_session: AsyncSession):
    paginated_users = await get_users_service(page=1, page_size=1, db=testdb_session)
    assert paginated_users["data"] == []


async def test_update_user_info_service_username(testdb_session: AsyncSession, created_user: UserModel):
    new_user_info = UserInfoUpdateRequest(username="new_username")
    updated_user = await update_user_info_service(user_id=created_user.id, new_user_info=new_user_info,
                                                  db=testdb_session)
    assert updated_user.username == "new_username"
    assert updated_user.email == created_user.email


async def test_update_user_password_service(testdb_session: AsyncSession, created_user: UserModel):
    new_password = "new_secure_password!@#"
    new_password_info = UserPasswordUpdateRequest(
        # Since created user saves hashed_password only
        current_password=DEFAULT_PASSWORD,
        new_password=SecretStr(new_password)
    )
    original_hash = created_user.hashed_password

    updated_user = await update_user_password_service(
        user_id=created_user.id,
        new_password_info=new_password_info,
        db=testdb_session
    )

    assert updated_user.hashed_password != original_hash
    assert verify_password(new_password, updated_user.hashed_password)


async def test_update_user_info_service_no_changes(testdb_session: AsyncSession, created_user: UserModel):
    new_user_info = UserInfoUpdateRequest()
    updated_user = await update_user_info_service(
        user_id=created_user.id,
        new_user_info=new_user_info,
        db=testdb_session
    )
    assert updated_user.username == created_user.username
    assert updated_user.hashed_password == created_user.hashed_password


async def test_update_user_info_service_not_found(testdb_session: AsyncSession):
    non_existent_id = uuid.uuid4()
    new_user_info = UserInfoUpdateRequest(username="newuser")
    with pytest.raises(InstanceNotFoundException):
        await update_user_info_service(user_id=non_existent_id, new_user_info=new_user_info, db=testdb_session)


async def test_update_user_password_service_reuse_error(testdb_session: AsyncSession, created_user: UserModel):
    new_password_info = UserPasswordUpdateRequest(
        current_password=DEFAULT_PASSWORD,
        new_password=DEFAULT_PASSWORD
    )

    with pytest.raises(PasswordReuseException):
        await update_user_password_service(
            user_id=created_user.id,
            new_password_info=new_password_info,
            db=testdb_session
        )


async def test_delete_user_service_success(testdb_session: AsyncSession, created_user: UserModel):
    await delete_user_service(user_id=created_user.id, db=testdb_session)
    user = await testdb_session.get(UserModel, created_user.id)
    assert user is None


async def test_delete_user_service_not_found(testdb_session: AsyncSession):
    non_existent_id = uuid.uuid4()
    with pytest.raises(InstanceNotFoundException):
        await delete_user_service(user_id=non_existent_id, db=testdb_session)
