from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    HOST: str
    PORT: int
    RELOAD: bool

    ORIGINS: list[str]

    # Limits
    MAX_PAGE_SIZE: int
