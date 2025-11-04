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


class PasswordReuseException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current password"
        )


class DBSessionNotInitializedException(Exception):
    def __init__(self):
        detail = "DBSessionManager is not initialized!"
        logger.error(detail)
        super().__init__(detail)
