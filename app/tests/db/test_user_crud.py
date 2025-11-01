import uuid

import pytest
import pytest_asyncio
from fastapi import HTTPException
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.crud.user import (
    create_user_crud,
    get_user_crud,
    get_users_crud,
    update_user_crud,
    delete_user_crud
)
from app.db.models.user import User as UserModel
from app.schemas.user import SignUpRequest, UserUpdateRequest

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def created_user(testdb_session: AsyncSession) -> UserModel:
    user_info = SignUpRequest(
        email="test@example.com",
        username="testuser",
        password=SecretStr("123456789")
    )
    user = await create_user_crud(user_info, db=testdb_session)
    return user


async def test_create_user_crud_success(testdb_session: AsyncSession):
    user_info = SignUpRequest(
        email="newuser@example.com",
        username="newuser",
        password=SecretStr("123456789")
    )
    user = await create_user_crud(user_info, db=testdb_session)

    assert user.id is not None
    assert user.email == "newuser@example.com"
    assert user.username == "newuser"
    assert verify_password("123456789", user.hashed_password)

    user_in_db = await testdb_session.get(UserModel, user.id)
    assert user_in_db is not None
    assert user_in_db.email == "newuser@example.com"


async def test_create_user_crud_duplicate_email(
        testdb_session: AsyncSession,
        created_user: UserModel,
):
    user_info_duplicate = SignUpRequest(
        email=created_user.email,
        username="anotheruser",
        password=SecretStr("password123")
    )
    with pytest.raises(HTTPException) as exc_info:
        await create_user_crud(user_info_duplicate, db=testdb_session)

    assert exc_info.value.status_code == 400
    assert "Record already exists" in exc_info.value.detail


async def test_get_user_crud_success(testdb_session: AsyncSession, created_user: UserModel):
    user_from_db = await get_user_crud(created_user.id, db=testdb_session)
    assert user_from_db.id == created_user.id
    assert user_from_db.email == created_user.email


async def test_get_user_crud_not_found(testdb_session: AsyncSession):
    non_existent_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await get_user_crud(non_existent_id, db=testdb_session)

    assert exc_info.value.status_code == 404
    assert "User not found" in exc_info.value.detail


# Testing both first and other pages
@pytest.mark.parametrize(
    "page, page_size, expected_has_next, expected_has_prev",
    [
        (1, 1, True, False),  # first page
        (2, 1, False, True),  # second (last) page
    ]
)
async def test_get_users_crud_pagination(testdb_session, page, page_size, expected_has_next, expected_has_prev):
    user1_info = SignUpRequest(email="user1@example.com", username="user1", password=SecretStr("123456789"))
    user2_info = SignUpRequest(email="user2@example.com", username="user2", password=SecretStr("123456789"))
    await create_user_crud(user1_info, db=testdb_session)
    await create_user_crud(user2_info, db=testdb_session)

    paginated_users = await get_users_crud(page=page, page_size=page_size, db=testdb_session)

    assert paginated_users["page"] == page
    assert paginated_users["page_size"] == page_size
    assert paginated_users["has_next"] is expected_has_next
    assert paginated_users["has_prev"] is expected_has_prev

    users = paginated_users["data"]
    assert len(users) == 1
    assert users[0].email in ["user1@example.com", "user2@example.com"]


async def test_get_users_crud_with_pagination_no_users(testdb_session: AsyncSession):
    paginated_users = await get_users_crud(page=1, page_size=1, db=testdb_session)
    assert paginated_users["data"] == []


async def test_update_user_crud_username(testdb_session: AsyncSession, created_user: UserModel):
    update_data = UserUpdateRequest(username="new_username")
    updated_user = await update_user_crud(created_user.id, update_data, db=testdb_session)
    assert updated_user.username == "new_username"
    assert updated_user.email == created_user.email  # email unchanged


async def test_update_user_crud_password(testdb_session: AsyncSession, created_user: UserModel):
    new_password = "new_secure_password!@#"
    update_data = UserUpdateRequest(password=SecretStr(new_password))
    original_hash = created_user.hashed_password

    updated_user = await update_user_crud(created_user.id, update_data, db=testdb_session)
    assert updated_user.hashed_password != original_hash
    assert verify_password(new_password, updated_user.hashed_password)


async def test_update_user_crud_no_changes(testdb_session: AsyncSession, created_user: UserModel):
    update_data = UserUpdateRequest()
    updated_user = await update_user_crud(created_user.id, update_data, db=testdb_session)
    assert updated_user.username == created_user.username
    assert updated_user.hashed_password == created_user.hashed_password


async def test_update_user_crud_not_found(testdb_session: AsyncSession):
    non_existent_id = uuid.uuid4()
    update_data = UserUpdateRequest(username="newuser")
    with pytest.raises(HTTPException) as exc_info:
        await update_user_crud(non_existent_id, update_data, db=testdb_session)
    assert exc_info.value.status_code == 404
    assert "User not found" in exc_info.value.detail


async def test_delete_user_crud_success(testdb_session: AsyncSession, created_user: UserModel):
    await delete_user_crud(created_user.id, db=testdb_session)
    user_in_db = await testdb_session.get(UserModel, created_user.id)
    assert user_in_db is None
    with pytest.raises(HTTPException) as exc_info:
        await get_user_crud(created_user.id, db=testdb_session)
    assert exc_info.value.status_code == 404


async def test_delete_user_crud_not_found(testdb_session: AsyncSession):
    non_existent_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await delete_user_crud(non_existent_id, db=testdb_session)
    assert exc_info.value.status_code == 404
    assert "User not found" in exc_info.value.detail
