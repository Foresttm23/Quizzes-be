from pydantic import computed_field
from pydantic_settings import BaseSettings


class RedisSettings(BaseSettings):
    # Redis
    REDIS_PASSWORD: str
    REDIS_DB: int

    @computed_field
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@redis:6379/{self.REDIS_DB}"
