import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import NullPool, text

from app.core.config import settings
from app.db.postgres import DBSessionManager


@pytest.fixture(scope="session")
def mock_database_url_for_alembic():
    """
    Ensures that the alembic 'upgrade' executes on the right (testdb in this case) database.
    A helper fixture for settings override.
    """
    original = settings.DB.DATABASE_URL
    try:
        type(settings.DB).DATABASE_URL = settings.TESTDB.TEST_DATABASE_URL
        yield
    finally:
        type(settings.DB).DATABASE_URL = original


@pytest.fixture(scope="session", autouse=True)
def run_migrations(mock_database_url_for_alembic):
    """
    Runs alembic migrations for testdb.
    Main fixture to ensure testdb is up to date.
    """
    config = Config("alembic.ini")
    # At first this overrides the "sqlalchemy.url", but after the "upgrade" command
    # alembic/env.py settings overrides the url again, and will ultimately upgrade
    # the main database instead of the test one
    ## config.set_main_option("sqlalchemy.url", settings.TESTDB.TEST_DATABASE_URL)
    command.upgrade(config, "head")


@pytest_asyncio.fixture(scope="session")
async def test_session_manager():
    """
    Creates a session manager for the testdb.
    A helper fixture for testdb_session fixture.
    """
    # NullPool ensures that the connections won't be shared/reused
    # so each test is in a clean state,
    # "must have" for async db environment
    test_session_manager = DBSessionManager(settings.TESTDB.TEST_DATABASE_URL, {"poolclass": NullPool})
    yield test_session_manager
    await test_session_manager.close()


@pytest_asyncio.fixture(scope="function")
async def testdb_session(test_session_manager):
    """
    Creates a session manager for the testdb.
    Main fixture to execute tests in a testdb.
    """
    async with test_session_manager.session() as session:
        yield session


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_testdb(testdb_session):
    """
    Ensures that we start from the clean db on each function execute.
    Main fixture to ensure tests execute in a 'clean' state.
    """
    await testdb_session.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE;"))
    await testdb_session.commit()
