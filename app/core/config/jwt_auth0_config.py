from pydantic_settings import BaseSettings


class Auth0JWTSettings(BaseSettings):
    AUTH0_JWKS_ENDPOINT: str = "https://url/.well-known/jwks.json"
    AUTH0_JWT_ALGORITHM: str = "RS256"
    AUTH0_JWT_AUDIENCE: str = "https://myapp.com/api"
