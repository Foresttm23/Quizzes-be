import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.company.company_model import Company as CompanyModel
from app.db.models.user.user_model import User as UserModel
from app.schemas.company.company_schema import CompanyCreateRequestSchema
from app.services.company.company_service import CompanyService
from app.services.company.member_service import CompanyMemberService

pytestmark = pytest.mark.asyncio

DEFAULT_COMPANY_NAME = "TestCompany Inc."
DEFAULT_COMPANY_DESCRIPTION = "A default company for testing."


@pytest_asyncio.fixture
async def company_owner(created_user: UserModel) -> UserModel:
    return created_user


@pytest_asyncio.fixture
async def company_owner_other(created_user_other: UserModel) -> UserModel:
    return created_user_other


@pytest_asyncio.fixture
async def test_company_service(
        test_company_member_service: CompanyMemberService, testdb_session: AsyncSession
) -> CompanyService:
    """Fixture to provide the CompanyService instance wired to the test database."""
    return CompanyService(
        db=testdb_session, company_member_service=test_company_member_service
    )


@pytest_asyncio.fixture
async def created_company(
        test_company_service: CompanyService,
        company_owner: UserModel,
        testdb_session: AsyncSession,
) -> CompanyModel:
    """Creates and returns a default Company instance for testing."""
    company_info = CompanyCreateRequestSchema(
        name=DEFAULT_COMPANY_NAME,
        description=DEFAULT_COMPANY_DESCRIPTION,
        is_visible=True,
    )
    company = await test_company_service.create_company(
        acting_user_id=company_owner.id, company_info=company_info
    )
    return company
