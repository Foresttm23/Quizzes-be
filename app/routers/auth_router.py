from datetime import timedelta

from fastapi import APIRouter, status

from app.core.config import settings
from app.core.dependencies import DBSessionDep, JWTDep
from app.core.exceptions import NotProvidedPasswordOrEmailException
from app.schemas.user_schemas.user_request_schema import SignUpRequest, SignInRequest
from app.schemas.user_schemas.user_response_schema import UserDetailsResponse, TokenResponse
from app.services.user_service import UserService
from app.utils.jwt_utils import create_access_token
from app.utils.jwt_utils import handle_jwt_sign_in, handle_email_password_sign_in

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserDetailsResponse)
async def register(db: DBSessionDep, user_info: SignUpRequest):
    """Endpoint for creating a user"""
    user_service = UserService(db=db)
    user = await user_service.create_user(user_info=user_info)
    return user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def sign_in(db: DBSessionDep, sign_in_data: SignInRequest = None, jwt_payload: JWTDep = None):
    """
    Endpoint for authenticating a user
    """
    user_service = UserService(db=db)

    if jwt_payload:
        user = await handle_jwt_sign_in(user_service=user_service, jwt_payload=jwt_payload)
    elif sign_in_data.email and sign_in_data.password:
        user = await handle_email_password_sign_in(user_service=user_service, sign_in_data=sign_in_data)
    else:
        raise NotProvidedPasswordOrEmailException()

    access_token_expires = timedelta(minutes=settings.LOCAL_JWT.LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"id": str(user.id), "email": user.email, "auth_provider": user.auth_provider},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
