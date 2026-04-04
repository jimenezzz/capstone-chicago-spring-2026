import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status

from shared.config import get_settings


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${salt.hex()}${derived.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = password_hash.split("$", 2)
    except ValueError:
        return False

    if algorithm != "scrypt":
        return False

    derived = hashlib.scrypt(password.encode("utf-8"), salt=bytes.fromhex(salt_hex), n=16384, r=8, p=1)
    return secrets.compare_digest(derived.hex(), digest_hex)


def create_access_token(*, user_id: int, username: str, role: str) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.auth_token_ttl_minutes)
    payload = {"sub": str(user_id), "username": username, "role": role, "exp": expires_at}
    token = jwt.encode(payload, settings.auth_secret_key, algorithm="HS256")
    return token, expires_at


def decode_access_token(token: str) -> dict[str, str]:
    try:
        payload = jwt.decode(token, get_settings().auth_secret_key, algorithms=["HS256"])
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return payload
