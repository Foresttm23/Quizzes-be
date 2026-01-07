from uuid import UUID, uuid4

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    ORIGINS: list[str] = ["http://other.com", "https://other.com"]
    UUID_TRANSFORM_SECRET: UUID = uuid4()

    # Limits
    MAX_PAGE_SIZE: int = 100


class DBSettings(BaseSettings):
    # PostgresSQL
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "passw"
    POSTGRES_DB: str = "my_db"

    @computed_field
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@postgres:5432/{self.POSTGRES_DB}"


class TestDBSettings(BaseSettings):
    # Test PostgresSQL
    TEST_POSTGRES_USER: str = "test_postgres"
    TEST_POSTGRES_PASSWORD: str = "passw"
    TEST_POSTGRES_DB: str = "db_test"

    @computed_field
    def TEST_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.TEST_POSTGRES_USER}:{self.TEST_POSTGRES_PASSWORD}@test_postgres:5432/{self.TEST_POSTGRES_DB}"


class Auth0JWTSettings(BaseSettings):
    AUTH0_JWKS_ENDPOINT: str = "https://url/.well-known/jwks.json"
    AUTH0_JWT_ALGORITHM: str = "RS256"
    AUTH0_JWT_AUDIENCE: str = "https://myapp.com/api"


class LocalJWTSettings(BaseSettings):
    LOCAL_JWT_SECRET: str = "mysecretkey"
    LOCAL_JWT_ALGORITHM: str = "HS256"
    LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    LOCAL_REFRESH_TOKEN_SECRET: str = "myothersecretkey"
    LOCAL_REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class RedisSettings(BaseSettings):
    # Redis
    REDIS_PASSWORD: str = "mysecretpassword"
    REDIS_DB: int = 0

    @computed_field
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@redis:6379/{self.REDIS_DB}"


class Settings(BaseSettings):
    APP: AppSettings = AppSettings()
    DB: DBSettings = DBSettings()
    TESTDB: TestDBSettings = TestDBSettings()
    LOCAL_JWT: LocalJWTSettings = LocalJWTSettings()
    AUTH0_JWT: Auth0JWTSettings = Auth0JWTSettings()
    REDIS: RedisSettings = RedisSettings()

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
