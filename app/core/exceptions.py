from fastapi import HTTPException, status

from app.core.logger import logger


class RecordAlreadyExistsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Record already exists"
        )


class InstanceNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


class UserIncorrectPasswordOrEmail(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incorrect password or email"
        )


class PasswordReuseException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current password"
        )


class InvalidSQLModelFieldNameException(HTTPException):
    def __init__(self, field_name: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid field name '{field_name}' for SQLModel"
        )


class InvalidJWTToken(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired JWT token"
        )


class DBSessionNotInitializedException(Exception):
    def __init__(self):
        detail = "DBSessionManager is not initialized!"
        logger.error(detail)
        super().__init__(detail)
