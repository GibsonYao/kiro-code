"""Authentication API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.security import verify_refresh_token
from app.models.user import User
from app.schemas.auth import (
    EmailLoginRequest,
    EmailRegisterRequest,
    MessageResponse,
    PhoneLoginRequest,
    RefreshTokenRequest,
    SendCodeRequest,
    TokenResponse,
    UserResponse,
    WechatLoginRequest,
)
from app.services.auth_service import (
    create_user_with_email,
    find_or_create_user_by_openid,
    find_or_create_user_by_phone,
    find_user_by_email,
    generate_tokens,
    get_user_by_id,
    get_wechat_openid,
    verify_password,
)
from app.services.sms_service import generate_verification_code, verify_code

router = APIRouter()


@router.post("/wechat-login", response_model=TokenResponse)
async def wechat_login(
    body: WechatLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """WeChat mini-program login.

    Exchange wx.login() code for openid, find or create user, return JWT tokens.
    """
    wechat_data = await get_wechat_openid(body.code)
    if wechat_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="WeChat login failed: invalid code",
        )

    openid = wechat_data["openid"]
    unionid = wechat_data.get("unionid")

    user = await find_or_create_user_by_openid(db, openid, unionid)
    return generate_tokens(user)


@router.post("/send-code", response_model=MessageResponse)
async def send_code(body: SendCodeRequest):
    """Send SMS verification code to the given phone number."""
    code = generate_verification_code(body.phone)
    # In demo mode, return the code in the response for testing
    return MessageResponse(message=f"验证码已发送 (demo: {code})")


@router.post("/phone-login", response_model=TokenResponse)
async def phone_login(
    body: PhoneLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Phone number + verification code login.

    Verify the SMS code, find or create user, return JWT tokens.
    """
    if not verify_code(body.phone, body.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="验证码无效或已过期",
        )

    user = await find_or_create_user_by_phone(db, body.phone)
    return generate_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using a valid refresh token."""
    user_id_str = verify_refresh_token(body.refresh_token)
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = await get_user_by_id(db, uuid.UUID(user_id_str))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return generate_tokens(user)


@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(
    db: AsyncSession = Depends(get_db),
):
    """Demo login - creates or finds a demo user, no credentials needed."""
    from app.core.config import settings
    if not settings.DEBUG:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    # Find or create demo user
    demo_email = "demo@example.com"
    user = await find_user_by_email(db, demo_email)
    if user is None:
        user = await create_user_with_email(db, demo_email, "demo123", "Demo用户")
        user.is_admin = True
        await db.flush()

    return generate_tokens(user)


@router.post("/register", response_model=TokenResponse)
async def email_register(
    body: EmailRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new account with email and password."""
    existing = await find_user_by_email(db, body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该邮箱已注册",
        )

    user = await create_user_with_email(db, body.email, body.password, body.nickname)
    return generate_tokens(user)


@router.post("/email-login", response_model=TokenResponse)
async def email_login(
    body: EmailLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password."""
    user = await find_user_by_email(db, body.email)
    if user is None or user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    return generate_tokens(user)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user
