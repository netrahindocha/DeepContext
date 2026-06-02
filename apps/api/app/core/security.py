from datetime import UTC, datetime, timedelta

from jose import jwt
from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    secret_key: str,
    algorithm: str,
    expires_delta: timedelta,
) -> str:
    expire = datetime.now(UTC) + expires_delta
    payload = {
        "sub": subject,
        "exp": expire,
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)
