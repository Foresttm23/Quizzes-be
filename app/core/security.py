from datetime import datetime, timedelta, timezone

from jose import jwt
from pwdlib import PasswordHash

from app.core.config import settings

pwd_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that hashed_password and plain_password are equal"""
    return pwd_hasher.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT.JWT_SECRET, algorithm=settings.JWT.JWT_ALGORITHM)

    return encoded_jwt
