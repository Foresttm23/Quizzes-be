from pydantic_settings import BaseSettings


class JWTSettings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
