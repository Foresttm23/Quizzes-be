from pydantic import computed_field
from pydantic_settings import BaseSettings


class DBSettings(BaseSettings):
    # PostgresSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "passw"
    POSTGRES_DB: str = "my_db"

    @computed_field
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@postgres:5432/{self.POSTGRES_DB}"
