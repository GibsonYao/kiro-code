"""Authentication service layer."""

import hashlib
import uuid
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt (simple demo implementation)."""
    salted = f"xiaozao_{password}_butler"
    return hashlib.sha256(salted.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(plain_password) == hashed_password


async def get_wechat_openid(code: str) -> dict[str, Any] | None:
    """Exchange WeChat login code for openid via WeChat API.

    Args:
        code: The login code from wx.login().

    Returns:
        Dict with openid and session_key, or None on failure.
    """
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.WECHAT_APP_ID,
        "secret": settings.WECHAT_APP_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    if "openid" in data:
        return data
    return None


async def find_or_create_user_by_openid(
    db: AsyncSession, openid: str, unionid: str | None = None
) -> User:
    """Find existing user by openid or create a new one.

    Args:
        db: Database session.
        openid: WeChat openid.
        unionid: WeChat unionid (optional).

    Returns:
        The User instance.
    """
    stmt = select(User).where(User.openid == openid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            openid=openid,
            unionid=unionid,
            is_admin=False,
        )
        db.add(user)
        await db.flush()

    return user


async def find_or_create_user_by_phone(db: AsyncSession, phone: str) -> User:
    """Find existing user by phone or create a new one.

    Args:
        db: Database session.
        phone: Mobile phone number.

    Returns:
        The User instance.
    """
    stmt = select(User).where(User.phone == phone)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            phone=phone,
            is_admin=False,
        )
        db.add(user)
        await db.flush()

    return user


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Get user by ID.

    Args:
        db: Database session.
        user_id: The user's UUID.

    Returns:
        User instance or None.
    """
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def generate_tokens(user: User) -> dict[str, str]:
    """Generate access and refresh tokens for a user.

    Args:
        user: The User instance.

    Returns:
        Dict with access_token, refresh_token, and token_type.
    """
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def find_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Find user by email.

    Args:
        db: Database session.
        email: Email address.

    Returns:
        User instance or None.
    """
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user_with_email(
    db: AsyncSession, email: str, password: str, nickname: str | None = None
) -> User:
    """Create a new user with email and password.

    Args:
        db: Database session.
        email: Email address.
        password: Plain text password (will be hashed).
        nickname: Optional nickname.

    Returns:
        The created User instance.
    """
    user = User(
        email=email,
        password_hash=hash_password(password),
        nickname=nickname or email.split("@")[0],
        is_admin=False,
    )
    db.add(user)
    await db.flush()
    return user
