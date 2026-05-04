"""Password hashing and JWT helpers.

Uses the `bcrypt` package directly (avoids passlib + bcrypt 4.x compatibility issues).
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError

from configs.settings import get_settings

# bcrypt has a 72-byte limit for the password input.
BCRYPT_MAX_PASSWORD_BYTES = 72


def _password_bytes(plain: str) -> bytes:
    b = plain.encode("utf-8")
    if len(b) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Password must be at most {BCRYPT_MAX_PASSWORD_BYTES} bytes in UTF-8 (bcrypt limit)."
        )
    return b


def hash_password(plain: str) -> str:
    pw = _password_bytes(plain)
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        pw = _password_bytes(plain)
    except ValueError:
        return False
    try:
        return bcrypt.checkpw(pw, password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


def create_access_token(
    *,
    subject: str,
    role_name: str,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    now = datetime.now(UTC)
    now_ts = int(now.timestamp())
    exp_ts = int((now + expires_delta).timestamp())
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role_name,
        "iat": now_ts,
        "exp": exp_ts,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def decode_token_safe(token: str) -> dict[str, Any] | None:
    try:
        return decode_token(token)
    except InvalidTokenError:
        return None
