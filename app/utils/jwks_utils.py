import requests

from app.core.config import settings


# Later we can create a "task" that would every hour fetch keys from the endpoint
# Or a simple variable with time or even Redis caching.
def get_jwks():
    return requests.get(settings.AUTH0_JWT.AUTH0_JWKS_ENDPOINT).json()["keys"]


def find_public_key(kid: str) -> dict | None:
    for key in get_jwks():
        if key["kid"] == kid:
            return key

    return None
