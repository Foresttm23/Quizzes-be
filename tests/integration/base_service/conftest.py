import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User as UserModel
from .test_base_service_setup import (
    _TestService,
    _TestUserRepository,
    _TestCreateSchema,
)


@pytest.fixture(scope="function")
def test_base_service(testdb_session: AsyncSession) -> _TestService:
    # Even though we test BaseService, UserModel here is solely for verifying crud operations.
    repo = _TestUserRepository(db=testdb_session, model=UserModel)
    return _TestService(repo=repo)


@pytest_asyncio.fixture
async def created_instance(test_base_service: _TestService) -> UserModel:
    instance_info = _TestCreateSchema(
        email="instance@example.com", username="instanceuser"
    )
    instance = await test_base_service.helper_create_instance(data=instance_info)
    return instance
