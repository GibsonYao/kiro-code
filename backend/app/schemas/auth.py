"""Auth-related Pydantic schemas."""

import uuid

from pydantic import BaseModel, EmailStr, Field


# ─── Request Schemas ───────────────────────────────────────────────────────────


class WechatLoginRequest(BaseModel):
    """Request body for WeChat mini-program login."""

    code: str = Field(..., description="WeChat login code from wx.login()")


class PhoneLoginRequest(BaseModel):
    """Request body for phone + verification code login."""

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="Chinese mobile number")
    code: str = Field(..., min_length=4, max_length=6, description="SMS verification code")


class SendCodeRequest(BaseModel):
    """Request body for sending SMS verification code."""

    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="Chinese mobile number")


class EmailRegisterRequest(BaseModel):
    """Request body for email registration."""

    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password")
    nickname: str | None = Field(None, max_length=64, description="Nickname")


class EmailLoginRequest(BaseModel):
    """Request body for email + password login."""

    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=1, description="Password")


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""

    refresh_token: str = Field(..., description="JWT refresh token")


# ─── Response Schemas ──────────────────────────────────────────────────────────


class TokenResponse(BaseModel):
    """Response containing JWT tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Response containing user information."""

    id: uuid.UUID
    openid: str | None = None
    phone: str | None = None
    email: str | None = None
    nickname: str | None = None
    avatar_url: str | None = None
    is_admin: bool = False

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
