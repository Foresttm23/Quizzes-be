import uuid
from typing import cast

import pytest
from app.core.exceptions import InstanceNotFoundException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User as UserModel
from .test_base_service_setup import _TestService, _TestCreateSchema, _TestUpdateSchema

pytestmark = pytest.mark.asyncio


async def test_fetch_instance_success(
        test_base_service: _TestService, created_instance: UserModel
):
    fetched_instance = await test_base_service.repo.get_instance_by_field_or_404(
        field=UserModel.id, value=created_instance.id
    )

    assert fetched_instance.id == created_instance.id
    fetched_user = cast(UserModel, fetched_instance)
    assert fetched_user.email == created_instance.email
    assert fetched_user.username == created_instance.username


async def test_fetch_instance_not_found(test_base_service: _TestService):
    non_existent_id = uuid.uuid4()
    with pytest.raises(InstanceNotFoundException):
        await test_base_service.repo.get_instance_by_field_or_404(
            field=UserModel.id, value=non_existent_id
        )


# Testing both first and other pages
@pytest.mark.parametrize(
    "page, page_size, expected_has_next, expected_has_prev",
    [
        (1, 1, True, False),  # first page
        (2, 1, False, True),
        # second (last) page
    ],
)
async def test_fetch_instances_paginated(
        test_base_service: _TestService,
        page,
        page_size,
        expected_has_next,
        expected_has_prev,
):
    await test_base_service.helper_create_instance(
        _TestCreateSchema(email="1@example.com", username="user1")
    )
    await test_base_service.helper_create_instance(
        _TestCreateSchema(email="2@example.com", username="user2")
    )

    paginated_results = await test_base_service.repo.get_instances_paginated(
        page=page, page_size=page_size
    )

    from app.core.logger import logger

    logger.critical(paginated_results["total"])

    assert paginated_results["page"] == page
    assert paginated_results["page_size"] == page_size
    assert paginated_results["has_next"] == expected_has_next
    assert paginated_results["has_prev"] == expected_has_prev

    instances = paginated_results["data"]
    assert len(instances) == 1
    assert hasattr(instances[0], "id")


async def test_fetch_instances_paginated_no_instances(test_base_service: _TestService):
    paginated_results = await test_base_service.repo.get_instances_paginated(
        page=1, page_size=1
    )
    assert paginated_results["data"] == []


async def test_update_instance_success(
        test_base_service: _TestService, created_instance: UserModel
):
    new_data = _TestUpdateSchema(username="new_instance_name")
    updated_instance = test_base_service._update_instance(
        instance=created_instance, new_data=new_data
    )
    await test_base_service.repo.save_and_refresh(updated_instance)

    assert updated_instance.username == "new_instance_name"
    assert updated_instance.email == created_instance.email
    assert updated_instance.id == created_instance.id


async def test_update_instance_no_changes(
        test_base_service: _TestService, created_instance: UserModel
):
    original_username = created_instance.username

    new_data = _TestUpdateSchema(
        username=created_instance.username, email=created_instance.email
    )
    updated_instance = test_base_service._update_instance(
        instance=created_instance, new_data=new_data
    )
    await test_base_service.repo.save_and_refresh(updated_instance)

    assert updated_instance.username == original_username
    assert updated_instance.email == created_instance.email
    # Since no changes were done, we can assert that both variables is one instance
    assert updated_instance is created_instance


async def test_delete_instance_success(
        test_base_service: _TestService,
        testdb_session: AsyncSession,
        created_instance: UserModel,
):
    instance_id = created_instance.id

    await test_base_service._delete_instance(instance=created_instance)
    await test_base_service.repo.commit()

    deleted_instance = await testdb_session.get(UserModel, instance_id)
    assert deleted_instance is None
