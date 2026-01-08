from fastapi import HTTPException, status
from logger import logger


class RecordAlreadyExistsException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail="Record already exists")


class InstanceNotFoundException(HTTPException):
    def __init__(self, instance_name: str, message: str | None = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"{instance_name} not found")


class UserIncorrectPasswordOrEmailException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect password or email")


class NotProvidedPasswordOrEmailException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide email and password or a jwt",
        )


class PasswordReuseException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password can't be the same as the current password",
        )


class InvalidPasswordException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current password",
        )


class InvalidSQLModelFieldNameException(HTTPException):
    def __init__(self, field_name: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid field name '{field_name}' for SQLModel",
        )


class InvalidJWTException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired JWT token",
        )


class InvalidJWTFieldsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided JWT has missing fields",
        )


class InvalidJWTRefreshException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid type of JWT token. Expected refresh token.",
        )


class ExternalAuthProviderException(HTTPException):
    def __init__(self, auth_provider: str, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authenticated via {auth_provider}, {message}.",
        )


class CompanyPermissionException(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")


class InvalidRecipientException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Different recipient for invitation/request",
        )


class PermissionDeniedException(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permissions: {message}")


class ResourceConflictException(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=f"Conflict: {message}")


class UserAlreadyInCompanyException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is already a member of this company",
        )


class NotAuthenticatedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


class UserIsNotACompanyMemberException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of a company",
        )


class DBSessionNotInitializedException(Exception):
    def __init__(self):
        detail = "DBSessionManager is not initialized!"
        logger.error(detail)
        super().__init__(detail)
