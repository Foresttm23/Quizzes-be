import os
from uuid import UUID, uuid4

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SharedConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class AppSettings(SharedConfig):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    DOCKER_MODE: bool = False

    ORIGINS: list[str] = ["http://other.com", "https://other.com"]
    UUID_TRANSFORM_SECRET: UUID = uuid4()

    # Limits
    MAX_PAGE_SIZE: int = 100


class DBSettings(SharedConfig):
    # PostgresSQL
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "passw"
    POSTGRES_DB: str = "my_db"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        # TODO pydantic settings
        if settings.APP.DOCKER_MODE:
            host = "postgres"
            port = 5432
        else:
            host = "localhost"
            port = 5433
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{host}:{port}/{self.POSTGRES_DB}"


class TestDBSettings(SharedConfig):
    # Test PostgresSQL
    TEST_POSTGRES_USER: str = "test_user"
    TEST_POSTGRES_PASSWORD: str = "passw"
    TEST_POSTGRES_DB: str = "db_test"

    @computed_field
    @property
    def TEST_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.TEST_POSTGRES_USER}:{self.TEST_POSTGRES_PASSWORD}@postgres:5432/{self.TEST_POSTGRES_DB}"


class Auth0JWTSettings(SharedConfig):
    AUTH0_JWKS_ENDPOINT: str = "https://url/.well-known/jwks.json"
    AUTH0_JWT_ALGORITHM: str = "RS256"
    AUTH0_JWT_AUDIENCE: str = "https://myapp.com/api"


class LocalJWTSettings(SharedConfig):
    LOCAL_JWT_SECRET: str = "mysecretkey"
    LOCAL_JWT_ALGORITHM: str = "HS256"
    LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    LOCAL_REFRESH_TOKEN_SECRET: str = "myothersecretkey"
    LOCAL_REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class RedisSettings(SharedConfig):
    # Redis
    REDIS_PASSWORD: str = "mysecretpassword"
    REDIS_DB: int = 0

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        is_docker = os.getenv("DOCKER_MODE", "false").lower() == "true"
        host = "redis" if is_docker else "localhost"
        return f"redis://:{self.REDIS_PASSWORD}@{host}:6379/{self.REDIS_DB}"


class Settings(BaseSettings):
    APP: AppSettings = AppSettings()
    DB: DBSettings = DBSettings()
    TESTDB: TestDBSettings = TestDBSettings()
    LOCAL_JWT: LocalJWTSettings = LocalJWTSettings()
    AUTH0_JWT: Auth0JWTSettings = Auth0JWTSettings()
    REDIS: RedisSettings = RedisSettings()


settings = Settings()
