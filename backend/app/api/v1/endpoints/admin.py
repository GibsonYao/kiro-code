"""Admin API endpoints for AI model configuration management."""

import json
import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import invalidate_ai_config_cache
from app.core.deps import get_current_user, get_db
from app.models.ai_config import AIModelConfig
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.admin import (
    AIConfigActivateResponse,
    AIConfigCreate,
    AIConfigListResponse,
    AIConfigResponse,
    AIConfigTestResponse,
    AIConfigUpdate,
)
from app.utils.encryption import decrypt_value, encrypt_value, mask_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Admin Permission Dependency (Task 14.6) ──────────────────────────────────


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that checks if the current user is an admin.

    Raises HTTP 403 if the user does not have admin privileges.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


# ─── Audit Logging Helper (Task 14.5) ─────────────────────────────────────────


async def _log_audit(
    db: AsyncSession,
    user_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: str | None = None,
) -> None:
    """Record an audit log entry for admin operations."""
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(log_entry)
    await db.flush()
    logger.info(
        f"Audit: user={user_id} action={action} resource={resource_type}/{resource_id}"
    )


# ─── Helper to build response with masked API key ─────────────────────────────


def _config_to_response(config: AIModelConfig) -> AIConfigResponse:
    """Convert an AIModelConfig model to a response with masked API key."""
    # Decrypt the stored API key to get the real value, then mask it
    try:
        real_key = decrypt_value(config.api_key)
        masked_key = mask_api_key(real_key)
    except Exception:
        masked_key = "****"

    return AIConfigResponse(
        id=config.id,
        config_key=config.config_key,
        provider=config.provider,
        model_name=config.model_name,
        api_key=masked_key,
        api_base_url=config.api_base_url,
        parameters=config.parameters,
        is_active=config.is_active,
        priority=config.priority,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


# ─── CRUD Endpoints (Task 14.1) ───────────────────────────────────────────────


@router.get("/ai-configs", response_model=AIConfigListResponse)
async def list_ai_configs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all AI model configurations (paginated)."""
    # Count total
    count_stmt = select(func.count()).select_from(AIModelConfig)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Fetch page
    offset = (page - 1) * page_size
    stmt = (
        select(AIModelConfig)
        .order_by(AIModelConfig.priority.desc(), AIModelConfig.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    configs = result.scalars().all()

    return AIConfigListResponse(
        items=[_config_to_response(c) for c in configs],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("/ai-configs", response_model=AIConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_config(
    data: AIConfigCreate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new AI model configuration."""
    # Encrypt the API key before storing
    encrypted_key = encrypt_value(data.api_key)

    config = AIModelConfig(
        config_key=data.config_key,
        provider=data.provider,
        model_name=data.model_name,
        api_key=encrypted_key,
        api_base_url=data.api_base_url,
        parameters=data.parameters,
        is_active=data.is_active,
        priority=data.priority,
    )
    db.add(config)
    await db.flush()
    await db.refresh(config)

    # Audit log
    await _log_audit(
        db,
        user_id=admin_user.id,
        action="create",
        resource_type="ai_config",
        resource_id=str(config.id),
        details=json.dumps({"config_key": data.config_key, "provider": data.provider, "model_name": data.model_name}),
    )

    return _config_to_response(config)


@router.put("/ai-configs/{config_id}", response_model=AIConfigResponse)
async def update_ai_config(
    config_id: uuid.UUID,
    data: AIConfigUpdate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing AI model configuration."""
    stmt = select(AIModelConfig).where(AIModelConfig.id == config_id)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )

    # Update fields that are provided
    update_data = data.model_dump(exclude_unset=True)
    changes = {}

    for field, value in update_data.items():
        if field == "api_key" and value is not None:
            # Encrypt the new API key
            value = encrypt_value(value)
            changes[field] = "(updated)"
        else:
            changes[field] = value
        setattr(config, field, value)

    await db.flush()
    await db.refresh(config)

    # Invalidate cache for this config_key
    await invalidate_ai_config_cache(config.config_key)

    # Audit log
    await _log_audit(
        db,
        user_id=admin_user.id,
        action="update",
        resource_type="ai_config",
        resource_id=str(config.id),
        details=json.dumps(changes, default=str),
    )

    return _config_to_response(config)


@router.delete("/ai-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_config(
    config_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an AI model configuration."""
    stmt = select(AIModelConfig).where(AIModelConfig.id == config_id)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )

    config_key = config.config_key

    # Audit log before deletion
    await _log_audit(
        db,
        user_id=admin_user.id,
        action="delete",
        resource_type="ai_config",
        resource_id=str(config.id),
        details=json.dumps({"config_key": config_key, "provider": config.provider}),
    )

    await db.delete(config)
    await db.flush()

    # Invalidate cache
    await invalidate_ai_config_cache(config_key)


# ─── Test Connectivity Endpoint (Task 14.2) ───────────────────────────────────


@router.post("/ai-configs/{config_id}/test", response_model=AIConfigTestResponse)
async def test_ai_config(
    config_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Test model connectivity by attempting a simple generation call."""
    stmt = select(AIModelConfig).where(AIModelConfig.id == config_id)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )

    # Decrypt the API key for testing
    try:
        api_key = decrypt_value(config.api_key)
    except Exception:
        return AIConfigTestResponse(
            success=False,
            message="API Key解密失败",
            response_time_ms=None,
        )

    # Attempt a simple connectivity test using httpx
    import httpx

    start_time = time.time()
    try:
        base_url = config.api_base_url or _get_default_base_url(config.provider)
        if not base_url:
            return AIConfigTestResponse(
                success=False,
                message=f"未配置API地址，provider: {config.provider}",
                response_time_ms=None,
            )

        # Try a simple chat completion request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config.model_name,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{base_url.rstrip('/')}/chat/completions"
            response = await client.post(url, json=payload, headers=headers)

        elapsed_ms = (time.time() - start_time) * 1000

        if response.status_code == 200:
            message = "连接成功"
            success = True
        else:
            message = f"API返回错误: HTTP {response.status_code}"
            success = False

    except httpx.TimeoutException:
        elapsed_ms = (time.time() - start_time) * 1000
        success = False
        message = "连接超时"
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        success = False
        message = f"连接失败: {str(e)}"

    # Audit log
    await _log_audit(
        db,
        user_id=admin_user.id,
        action="test",
        resource_type="ai_config",
        resource_id=str(config.id),
        details=json.dumps({"success": success, "message": message}),
    )

    return AIConfigTestResponse(
        success=success,
        message=message,
        response_time_ms=round(elapsed_ms, 2),
    )


def _get_default_base_url(provider: str) -> str | None:
    """Get default base URL for known providers."""
    defaults = {
        "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "openai": "https://api.openai.com/v1",
    }
    return defaults.get(provider.lower())


# ─── Activate/Deactivate Endpoint (Task 14.3) ─────────────────────────────────


@router.put("/ai-configs/{config_id}/activate", response_model=AIConfigActivateResponse)
async def toggle_ai_config_active(
    config_id: uuid.UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle the is_active field of an AI model configuration."""
    stmt = select(AIModelConfig).where(AIModelConfig.id == config_id)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在",
        )

    # Toggle active state
    config.is_active = not config.is_active
    await db.flush()
    await db.refresh(config)

    # Invalidate cache
    await invalidate_ai_config_cache(config.config_key)

    # Audit log
    await _log_audit(
        db,
        user_id=admin_user.id,
        action="activate" if config.is_active else "deactivate",
        resource_type="ai_config",
        resource_id=str(config.id),
        details=json.dumps({"is_active": config.is_active}),
    )

    status_text = "已激活" if config.is_active else "已停用"
    return AIConfigActivateResponse(
        id=config.id,
        is_active=config.is_active,
        message=f"配置{status_text}",
    )
