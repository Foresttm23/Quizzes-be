from pydantic_settings import BaseSettings


class LocalJWTSettings(BaseSettings):
    LOCAL_JWT_SECRET: str = "mysecretkey"
    LOCAL_JWT_ALGORITHM: str = "HS256"
    LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
