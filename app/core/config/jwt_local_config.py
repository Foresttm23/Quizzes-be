from pydantic_settings import BaseSettings


class LocalJWTSettings(BaseSettings):
    LOCAL_JWT_SECRET: str
    LOCAL_JWT_ALGORITHM: str
    LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES: int
