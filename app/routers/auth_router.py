from fastapi import APIRouter, status

from app.core.dependencies import AuthServiceDep, GetUserRefreshJWTDep
from app.core.exceptions import ExternalAuthProviderException
from app.schemas.user_schemas.user_request_schema import RegisterRequest, LoginRequest
from app.schemas.user_schemas.user_response_schema import UserDetailsResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserDetailsResponse)
async def register(auth_service: AuthServiceDep, register_data: RegisterRequest):
    """Endpoint for registering/creating a user"""
    user = await auth_service.register_user(sign_up_data=register_data)
    return user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(auth_service: AuthServiceDep, login_data: LoginRequest):
    """
    Endpoint for authenticating a user with password and email.
    For Auth0 log in call users/me or any with GetUserJWTDep.
    """
    user = await auth_service.handle_email_password_sign_in(sign_in_data=login_data)
    tokens = auth_service.create_token_pairs(user=user)
    return tokens


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_jwt(auth_service: AuthServiceDep, user: GetUserRefreshJWTDep):
    """
    Endpoint for refreshing a refresh token.
    Accepts refresh token.
    Returns both, refresh token and access token.
    """
    # Technically never raised, since external providers cannot be decoded with the local configuration.
    if user.auth_provider != "local":
        raise ExternalAuthProviderException(auth_provider=user.auth_provider, message="no local tokens issued")

    tokens = auth_service.create_token_pairs(user=user)
    return tokens
