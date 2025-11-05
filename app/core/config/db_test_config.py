from pydantic import computed_field
from pydantic_settings import BaseSettings


class TestDBSettings(BaseSettings):
    # Test PostgresSQL
    TEST_POSTGRES_USER: str
    TEST_POSTGRES_PASSWORD: str
    TEST_POSTGRES_DB: str

    @computed_field
    def TEST_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.TEST_POSTGRES_USER}:{self.TEST_POSTGRES_PASSWORD}@test_postgres:5432/{self.TEST_POSTGRES_DB}"
