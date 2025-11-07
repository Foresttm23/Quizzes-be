from pydantic_settings import BaseSettings


class Auth0JWTSettings(BaseSettings):
    AUTH0_JWKS_ENDPOINT: str
    AUTH0_JWT_ALGORITHM: str
    AUTH0_JWT_AUDIENCE: str
