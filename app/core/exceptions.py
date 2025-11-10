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


class FieldsNotProvidedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least 1 field."
        )


class UserIncorrectPasswordOrEmailException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incorrect password or email"
        )


class NotProvidedPasswordOrEmailException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide email and password or a jwt"
        )


class PasswordReuseException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current password"
        )


class InvalidPasswordException(HTTPException):
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


class InvalidJWTException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired JWT token"
        )


class CompanyPermissionException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can update the company"
        )


class DBSessionNotInitializedException(Exception):
    def __init__(self):
        detail = "DBSessionManager is not initialized!"
        logger.error(detail)
        super().__init__(detail)
