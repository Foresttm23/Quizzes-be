from pwdlib import PasswordHash

pwd_hasher = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that hashed_password and plain_password are equal"""
    return pwd_hasher.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_hasher.hash(password)
