from fastapi import APIRouter, status

from app.core.dependencies import JWTDep, AuthServiceDep, UserServiceDep
from app.core.exceptions import NotProvidedPasswordOrEmailException
from app.schemas.user_schemas.user_request_schema import SignUpRequest, SignInRequest
from app.schemas.user_schemas.user_response_schema import UserDetailsResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserDetailsResponse)
async def register(user_service: UserServiceDep, user_info: SignUpRequest):
    """Endpoint for creating a user"""
    user = await user_service.create_user(user_info=user_info)
    return user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def sign_in(auth_service: AuthServiceDep, sign_in_data: SignInRequest = None, jwt_payload: JWTDep = None):
    """
    Endpoint for authenticating a user
    """
    if jwt_payload:
        user = await auth_service.handle_jwt_sign_in(jwt_payload=jwt_payload)
    elif sign_in_data.email and sign_in_data.password:
        user = await auth_service.handle_email_password_sign_in(sign_in_data=sign_in_data)
    else:
        raise NotProvidedPasswordOrEmailException()

    access_token = auth_service.create_access_token(user=user)

    return {"access_token": access_token, "token_type": "bearer"}
