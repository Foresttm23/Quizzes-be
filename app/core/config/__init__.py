from pydantic_settings import BaseSettings, SettingsConfigDict

from .app_config import AppSettings
from .db_config import DBSettings
from .db_test_config import TestDBSettings
from .jwt_config import JWTSettings
from .redis_config import RedisSettings


class Settings(BaseSettings):
    APP: AppSettings = AppSettings()

    DB: DBSettings = DBSettings()
    TESTDB: TestDBSettings = TestDBSettings()

    JWT: JWTSettings = JWTSettings()

    REDIS: RedisSettings = RedisSettings()

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')


settings = Settings()
