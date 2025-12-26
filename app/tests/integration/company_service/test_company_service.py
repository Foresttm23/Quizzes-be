import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InstanceNotFoundException, RecordAlreadyExistsException, \
    UserIsNotACompanyMemberException
from app.db.models.company_model import Company as CompanyModel
from app.db.models.user_model import User as UserModel
from app.schemas.company_schemas.company_request_schema import CompanyCreateRequest, CompanyUpdateInfoRequest
from app.services.company_service import CompanyService

pytestmark = pytest.mark.asyncio

DEFAULT_COMPANY_NAME = "TestCompany Inc."
DEFAULT_COMPANY_DESCRIPTION = "A default company for testing."


async def test_create_company_success(testdb_session: AsyncSession, test_company_service: CompanyService,
                                      company_owner: UserModel):
    company_info = CompanyCreateRequest(name="New Company", description="Another testing company.", is_visible=True)
    company = await test_company_service.create_company(owner_id=company_owner.id, company_info=company_info)

    assert company.id is not None
    assert company.name == "New Company"
    assert company.members[0].user_id == company_owner.id
    assert company.description == "Another testing company."
    assert company.is_visible is True

    await testdb_session.refresh(company_owner)
    assert len(company_owner.companies) == 1
    assert company_owner.companies[0].company_id == company.id


async def test_create_company_duplicate_name(test_company_service: CompanyService, company_owner: UserModel,
                                             created_company: CompanyModel):
    company_info_duplicate = CompanyCreateRequest(name=created_company.name, description="Should Fail", is_visible=True)

    with pytest.raises(RecordAlreadyExistsException):
        await test_company_service.create_company(owner_id=company_owner.id, company_info=company_info_duplicate)


async def test_update_company_info_success(test_company_service: CompanyService, created_company: CompanyModel,
                                           company_owner: UserModel):
    new_info = CompanyUpdateInfoRequest(name="New Updated Name", description="Updated Description", is_visible=True)

    updated_company = await test_company_service.update_company(company_id=created_company.id,
                                                                owner_id=company_owner.id, company_info=new_info)
    assert updated_company.name == "New Updated Name"
    assert updated_company.description == "Updated Description"
    assert updated_company.members[0].user_id == company_owner.id
    assert updated_company.is_visible is not None


async def test_update_company_info_permission_error(test_company_service: CompanyService, created_company: CompanyModel,
                                                    company_owner_other: UserModel):
    new_info = CompanyUpdateInfoRequest(name="Attempted Update", description=None, is_visible=True)

    with pytest.raises(UserIsNotACompanyMemberException):
        await test_company_service.update_company(company_id=created_company.id, owner_id=company_owner_other.id,
                                                  company_info=new_info)


async def test_update_company_info_not_found(test_company_service: CompanyService, company_owner: UserModel):
    non_existent_id = uuid.uuid4()
    new_info = CompanyUpdateInfoRequest(name="Attempted Update", description=None, is_visible=None)

    with pytest.raises(InstanceNotFoundException):
        await test_company_service.update_company(company_id=non_existent_id, owner_id=company_owner.id,
                                                  company_info=new_info)


async def test_delete_company_success(test_company_service: CompanyService, testdb_session: AsyncSession,
                                      created_company: CompanyModel, company_owner: UserModel):
    """Basic deletion of the instance, but we have to check if the company deletion were made in cascade"""
    await test_company_service.delete_company(company_id=created_company.id, owner_id=company_owner.id)

    company = await testdb_session.get(CompanyModel, created_company.id)
    assert company is None
    assert company_owner.companies == []


async def test_delete_company_permission_error(test_company_service: CompanyService, created_company: CompanyModel,
                                               company_owner_other: UserModel):
    with pytest.raises(UserIsNotACompanyMemberException):
        await test_company_service.delete_company(company_id=created_company.id, owner_id=company_owner_other.id)


# ------------------------------------PRETTY MUCH OBSOLETE, SINCE BASE SERVICE ALREADY TESTS THIS------------------------------------
# -------------------------BUT SINCE IT INTERACTS MOSTLY WITH 2 MODELS (USER, COMPANY), CAN STILL BE USEFUL--------------------------

async def test_fetch_company_by_id_success(test_company_service: CompanyService, created_company: CompanyModel):
    company_from_db = await test_company_service.get_by_id(company_id=created_company.id)
    assert company_from_db.id == created_company.id
    assert company_from_db.name == created_company.name
    assert company_from_db.members[0].user_id == created_company.members[0].user_id


async def test_fetch_company_by_id_not_found(test_company_service: CompanyService):
    non_existent_id = uuid.uuid4()
    with pytest.raises(InstanceNotFoundException):
        await test_company_service.get_by_id(company_id=non_existent_id)


async def test_fetch_companies_paginated_success(test_company_service: CompanyService, company_owner: UserModel):
    company1_info = CompanyCreateRequest(name="Page 1 Co", description="Co 1", is_visible=True)
    company2_info = CompanyCreateRequest(name="Page 2 Co", description="Co 2", is_visible=True)
    await test_company_service.create_company(owner_id=company_owner.id, company_info=company1_info)
    await test_company_service.create_company(owner_id=company_owner.id, company_info=company2_info)

    paginated_companies = await test_company_service.get_companies_paginated(page=1, page_size=1)

    assert paginated_companies["page"] == 1
    assert len(paginated_companies["data"]) == 1
    assert paginated_companies["has_next"] is True


async def test_fetch_companies_paginated_no_companies(test_company_service: CompanyService):
    paginated_companies = await test_company_service.get_companies_paginated(page=1, page_size=1)
    assert paginated_companies["data"] == []


async def test_delete_company_not_found(test_company_service: CompanyService, company_owner: UserModel):
    non_existent_id = uuid.uuid4()

    with pytest.raises(InstanceNotFoundException):
        await test_company_service.delete_company(company_id=non_existent_id, owner_id=company_owner.id)
