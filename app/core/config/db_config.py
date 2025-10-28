from pydantic import computed_field
from pydantic_settings import BaseSettings


class DBSettings(BaseSettings):
    # PostgresSQL
    postgres_user: str
    postgres_password: str
    postgres_db: str
    # Debug
    echo_sql: bool

    @computed_field
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@postgres:5432/{self.postgres_db}"
