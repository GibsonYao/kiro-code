"""Security utilities (JWT token generation and verification)."""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings

# Token type constants
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Create a JWT access token.

    Args:
        subject: The token subject (typically user ID).
        extra_claims: Additional claims to include in the token.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": ACCESS_TOKEN_TYPE,
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a JWT refresh token.

    Args:
        subject: The token subject (typically user ID).

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": REFRESH_TOKEN_TYPE,
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: The JWT string to decode.

    Returns:
        Decoded payload dict, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> str | None:
    """Verify an access token and return the subject (user ID).

    Args:
        token: The JWT access token string.

    Returns:
        The subject string (user ID) if valid, None otherwise.
    """
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        return None
    return payload.get("sub")


def verify_refresh_token(token: str) -> str | None:
    """Verify a refresh token and return the subject (user ID).

    Args:
        token: The JWT refresh token string.

    Returns:
        The subject string (user ID) if valid, None otherwise.
    """
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != REFRESH_TOKEN_TYPE:
        return None
    return payload.get("sub")
