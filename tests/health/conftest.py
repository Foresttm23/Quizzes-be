import pytest

from core.config import settings
from core.database import init_db


# Since tests are now simple no need to init_db via original lifespan
@pytest.fixture()
def init_db_for_tests():
    init_db(settings.DB.DATABASE_URL)
