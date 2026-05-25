"""Admin API Pydantic schemas for AI model configuration management."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AIConfigCreate(BaseModel):
    """Schema for creating a new AI model configuration."""

    config_key: str = Field(..., max_length=64, description="Configuration key (e.g., 'text_generation')")
    provider: str = Field(..., max_length=64, description="AI provider name (e.g., 'dashscope', 'deepseek')")
    model_name: str = Field(..., max_length=128, description="Model name (e.g., 'qwen-turbo')")
    api_key: str = Field(..., max_length=512, description="API key for the provider")
    api_base_url: str | None = Field(None, max_length=512, description="Custom API base URL")
    parameters: dict | None = Field(None, description="Additional model parameters as JSON")
    is_active: bool = Field(True, description="Whether this config is active")
    priority: int = Field(0, description="Priority for fallback ordering (higher = preferred)")


class AIConfigUpdate(BaseModel):
    """Schema for updating an AI model configuration."""

    config_key: str | None = Field(None, max_length=64)
    provider: str | None = Field(None, max_length=64)
    model_name: str | None = Field(None, max_length=128)
    api_key: str | None = Field(None, max_length=512)
    api_base_url: str | None = Field(None, max_length=512)
    parameters: dict | None = None
    is_active: bool | None = None
    priority: int | None = None


class AIConfigResponse(BaseModel):
    """Schema for AI model configuration in API responses."""

    id: uuid.UUID
    config_key: str
    provider: str
    model_name: str
    api_key: str  # Will be masked (e.g., '****abcd')
    api_base_url: str | None
    parameters: dict | None
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIConfigListResponse(BaseModel):
    """Paginated list response for AI configs."""

    items: list[AIConfigResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class AIConfigTestResponse(BaseModel):
    """Response for model connectivity test."""

    success: bool
    message: str
    response_time_ms: float | None = None


class AIConfigActivateResponse(BaseModel):
    """Response for activate/deactivate toggle."""

    id: uuid.UUID
    is_active: bool
    message: str


class AuditLogResponse(BaseModel):
    """Schema for audit log entries."""

    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    resource_type: str
    resource_id: str | None
    details: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
