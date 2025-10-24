from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    origins: list[str]
    # PostgresSQL
    database_url: str
    echo_sql: bool  # Debug
    # Redis
    redis_url: str

    class Config:
        env_file = ".env"


settings = Settings()
