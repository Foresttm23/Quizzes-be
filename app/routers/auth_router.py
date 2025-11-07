from datetime import timedelta

from fastapi import APIRouter, status

from app.core.config import settings
from app.core.dependencies import DBSessionDep, VerifyTokenDep, OAuth2PasswordRequestFormDep
from app.core.exceptions import UserIncorrectPasswordOrEmail, InstanceNotFoundException
from app.schemas.user_schemas.user_request_schema import SignUpRequest
from app.schemas.user_schemas.user_response_schema import UserDetailsResponse, TokenResponse
from app.services.user_service import UserService
from app.utils.jwt_utils import create_access_token
from app.utils.password_utils import verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserDetailsResponse)
async def register(db: DBSessionDep, user_info: SignUpRequest):
    """Endpoint for creating a user"""
    user_service = UserService(db=db)
    user = await user_service.create_user(user_info=user_info)
    return user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(db: DBSessionDep, form_data: OAuth2PasswordRequestFormDep):
    user_service = UserService(db=db)

    # Checks if user exist byt itself, so the call checking user isn't needed
    # but might help in some unexpected situations
    user = await user_service.fetch_instance(field_name="email", field_value=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise UserIncorrectPasswordOrEmail()

    access_token_expires = timedelta(minutes=settings.JWT.LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserDetailsResponse, status_code=status.HTTP_200_OK)
async def get_me(db: DBSessionDep, user_jwt_sub: VerifyTokenDep):
    user_service = UserService(db=db)
    try:
        user = await user_service.fetch_instance(field_name="email", field_value=user_jwt_sub["email"])
    except InstanceNotFoundException:
        user = await user_service.create_user_from_jwt(user_info=user_jwt_sub)

    return user
