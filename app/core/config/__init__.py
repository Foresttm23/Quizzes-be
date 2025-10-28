from pydantic_settings import BaseSettings, SettingsConfigDict

from .app_config import AppSettings
from .db_config import DBSettings
from .redis_config import RedisSettings


class Settings(BaseSettings):
    app: AppSettings = AppSettings()
    db: DBSettings = DBSettings()
    redis: RedisSettings = RedisSettings()

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')


settings = Settings()
