from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    ORIGINS: list[str] = ["http://other.com", "https://other.com"]

    # Limits
    MAX_PAGE_SIZE: int = 100
