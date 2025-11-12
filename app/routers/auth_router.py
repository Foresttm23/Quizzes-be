from fastapi import APIRouter, status

from app.core.dependencies import LoginJWTDep, AuthServiceDep, JWTCredentialsDep, UserServiceDep
from app.schemas.user_schemas.user_request_schema import SignUpRequest, SignInRequest
from app.schemas.user_schemas.user_response_schema import UserDetailsResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserDetailsResponse)
async def register(auth_service: AuthServiceDep, user_info: SignUpRequest):
    """Endpoint for registering/creating a user"""
    user = await auth_service.register_user(user_info=user_info)
    return user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def sign_in(auth_service: AuthServiceDep, sign_in_data: SignInRequest | None = None,
                  jwt_payload: LoginJWTDep | None = None):
    """Endpoint for authenticating a user with either password and email or Auth0"""
    user = await auth_service.handle_sign_in(sign_in_data=sign_in_data, jwt_payload=jwt_payload)

    tokens = auth_service.create_token_pairs(user=user)
    return tokens


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_jwt(user_service: UserServiceDep, auth_service: AuthServiceDep, jwt_refresh_token: JWTCredentialsDep):
    """
    Endpoint for refreshing a refresh token.
    Returns both, refresh token and access token.
    """
    payload = auth_service.verify_refresh_token_and_get_payload(token=jwt_refresh_token)
    user = await user_service.fetch_user("id", payload["id"])
    tokens = auth_service.create_token_pairs(user=user)
    return tokens
