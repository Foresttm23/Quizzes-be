from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field


class Settings(BaseSettings):
    origins: list[str]
    # PostgresSQL
    postgres_user: str
    postgres_password: str
    postgres_db: str
    echo_sql: bool  # Debug
    # Redis
    redis_password: str
    redis_db: int

    model_config = SettingsConfigDict(env_file=".env")

    @computed_field
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@postgres:5432/{self.postgres_db}"

    @computed_field
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@redis:6379/{self.redis_db}"


settings = Settings()
