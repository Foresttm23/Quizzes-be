import pytest

from core.config import settings
from core.database import get_session_manager


# Since tests are now simple no need to init_db via original lifespan
@pytest.fixture()
def init_db_for_tests():
    get_session_manager(settings.DB.DATABASE_URL)
