import asyncio

from pwdlib import PasswordHash

pwd_hasher = PasswordHash.recommended()


async def hash_password(password: str) -> str:
    """Hash a password"""
    return await asyncio.to_thread(pwd_hasher.hash, password)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that hashed_password and plain_password are equal"""
    return await asyncio.to_thread(pwd_hasher.verify, plain_password, hashed_password)
