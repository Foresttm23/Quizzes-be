from enum import Enum


class AuthProviderEnum(str, Enum):
    AUTH0 = "auth0"
    LOCAL = "local"


class JWTTypeEnum(str, Enum):
    """Token type of local JWT"""
    ACCESS = "access"
    REFRESH = "refresh"
