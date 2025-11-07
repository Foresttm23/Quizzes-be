from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, jws

from app.core.config import settings
from app.core.exceptions import InvalidJWTToken
from app.utils.jwks_utils import find_public_key
from app.utils.jwt_utils import check_jwt_fields

# To prevent circular imports.
# Since I make dependency from verify_token.
security = HTTPBearer()
SecurityDep = Annotated[HTTPAuthorizationCredentials, Depends(security)]


def verify_token(token: SecurityDep) -> dict:
    jwt_token = token.credentials
    # Since we have 2 variation of registration we check them in order
    try:
        return verify_token_local(jwt_token)
    except InvalidJWTToken:
        # If this raises error, code stops
        return verify_token_auth0(jwt_token)


def verify_token_local(token: str) -> dict:
    try:
        # Decode handles expiration automatically
        payload = jwt.decode(token, settings.LOCAL_JWT.LOCAL_JWT_SECRET,
                             algorithms=[settings.LOCAL_JWT.LOCAL_JWT_ALGORITHM])
        email: str = payload.get("sub")

        if email is None:
            raise InvalidJWTToken()

        return {"email": email}
    except JWTError:
        raise InvalidJWTToken()


def verify_token_auth0(token: str):
    try:
        unverified_token = jws.get_unverified_header(token)
        public_key = find_public_key(unverified_token["kid"])
        if public_key is None:
            raise InvalidJWTToken()

        # Decode handles expiration automatically
        payload = jwt.decode(
            token=token,
            key=public_key,
            audience=settings.AUTH0_JWT.AUTH0_JWT_AUDIENCE,
            algorithms=settings.AUTH0_JWT.AUTH0_JWT_ALGORITHM,
        )

        email: str = payload.get("email")

        response = {"email": email}
        check_jwt_fields(response)

        return response
    except JWTError:
        raise InvalidJWTToken()
