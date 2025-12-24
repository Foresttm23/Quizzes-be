from pydantic_settings import BaseSettings, SettingsConfigDict

from .app_config import AppSettings
from .db_config import DBSettings
from .db_test_config import TestDBSettings
from .jwt_auth0_config import Auth0JWTSettings
from .jwt_local_config import LocalJWTSettings
from .redis_config import RedisSettings


class Settings(BaseSettings):
    APP: AppSettings = AppSettings()
    DB: DBSettings = DBSettings()
    TESTDB: TestDBSettings = TestDBSettings()
    LOCAL_JWT: LocalJWTSettings = LocalJWTSettings()
    AUTH0_JWT: Auth0JWTSettings = Auth0JWTSettings()
    REDIS: RedisSettings = RedisSettings()

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')


settings = Settings()
