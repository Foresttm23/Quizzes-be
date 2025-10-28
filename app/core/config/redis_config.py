from pydantic import computed_field
from pydantic_settings import BaseSettings


class RedisSettings(BaseSettings):
    # Redis
    redis_password: str
    redis_db: int

    @computed_field
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@redis:6379/{self.redis_db}"
