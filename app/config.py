from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    origins: list[str]

    class Config:
        env_file = ".env"


settings = Settings()
