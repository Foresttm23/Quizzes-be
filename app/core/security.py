from jose import JWTError, jwt, jws, JWSError

from app.core.config import settings
from app.core.exceptions import InvalidJWTException
from app.utils.jwks_utils import find_public_key
from app.utils.jwt_utils import check_jwt_fields, fill_jwt_fields_from_payload


def verify_token_and_get_payload(jwt_token: str) -> dict:
    # Since we have 2 variation of registration we check them in order
    try:
        # Local verification is used for all auth endpoints,
        # thus should be first in order
        return verify_local_token_and_get_payload(jwt_token)
    except InvalidJWTException:
        # If this raises error, code stops
        return verify_auth0_token_and_get_payload(jwt_token)


def verify_local_token_and_get_payload(token: str) -> dict:
    try:
        # Decode handles expiration automatically
        payload = jwt.decode(token, settings.LOCAL_JWT.LOCAL_JWT_SECRET,
                             algorithms=[settings.LOCAL_JWT.LOCAL_JWT_ALGORITHM])
    except JWTError:
        raise InvalidJWTException()

    response = fill_jwt_fields_from_payload(payload=payload)
    check_jwt_fields(response)

    return response


def verify_auth0_token_and_get_payload(token: str):
    try:
        unverified_token = jws.get_unverified_header(token)
        public_key = find_public_key(unverified_token["kid"])
        if public_key is None:
            raise InvalidJWTException()

        # Decode handles expiration automatically
        payload = jwt.decode(token=token, key=public_key, audience=settings.AUTH0_JWT.AUTH0_JWT_AUDIENCE,
                             algorithms=settings.AUTH0_JWT.AUTH0_JWT_ALGORITHM, )
    except (JWTError, JWSError, KeyError):
        raise InvalidJWTException()

    # Since Auth0 only issue an email
    email: str = payload.get("email")
    response = {"email": email}
    check_jwt_fields(response)

    return response
