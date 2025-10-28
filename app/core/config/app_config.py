from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    host: str
    port: int
    reload: bool

    origins: list[str]
