"""AI generation status API endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.tasks import celery_app
from app.tasks.ai_tasks import generate_image_task, generate_text_task

router = APIRouter()


# Celery state → API status mapping
_STATE_MAP: dict[str, str] = {
    "PENDING": "pending",
    "STARTED": "started",
    "SUCCESS": "completed",
    "FAILURE": "failed",
    "RETRY": "pending",
}


class GenerationStatusResponse(BaseModel):
    """Response schema for AI generation task status."""

    task_id: str
    status: str
    result: Optional[Any] = None


class RegenerateRequest(BaseModel):
    """Request body for regenerating AI content."""

    entity_type: str = Field(..., description="实体类型 (wish/goal/plan/task/action)")
    entity_id: str = Field(..., description="实体UUID")
    style: str | None = Field(None, description="图片风格")


class RegenerateResponse(BaseModel):
    """Response for regeneration request."""

    task_id: str


class ImageStyle(BaseModel):
    """Available image generation style."""

    id: str
    name: str
    description: str
    preview_url: str | None = None


class StylesResponse(BaseModel):
    """Response for available styles."""

    styles: list[ImageStyle]


@router.get("/generation/{task_id}/status", response_model=GenerationStatusResponse)
async def get_generation_status(task_id: str) -> GenerationStatusResponse:
    """Query the status of an AI generation task.

    Uses Celery AsyncResult to check the current state of the task.
    Maps Celery states to simplified API statuses:
    - PENDING → pending
    - STARTED → started
    - SUCCESS → completed
    - FAILURE → failed
    - RETRY → pending
    """
    async_result = celery_app.AsyncResult(task_id)
    celery_state = async_result.state

    status = _STATE_MAP.get(celery_state, "pending")

    result = None
    if celery_state == "SUCCESS":
        result = async_result.result
    elif celery_state == "FAILURE":
        # For failed tasks, include the error message
        result = str(async_result.result) if async_result.result else None

    return GenerationStatusResponse(
        task_id=task_id,
        status=status,
        result=result,
    )


@router.post("/regenerate-image", response_model=RegenerateResponse)
async def regenerate_image(
    body: RegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger regeneration of an entity's cover image."""
    style_hint = f"风格：{body.style}。" if body.style else ""
    prompt = f"为{body.entity_type}生成一张精美配图。{style_hint}要求色彩鲜明、构图精美。"

    task = generate_image_task.delay(
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        config_key="image_generation",
        prompt=prompt,
    )

    return RegenerateResponse(task_id=task.id)


@router.post("/regenerate-text", response_model=RegenerateResponse)
async def regenerate_text(
    body: RegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger regeneration of an entity's display text."""
    prompt = f"请为这个{body.entity_type}生成一段简洁有力、富有感染力的展示文案，30字以内。"

    task = generate_text_task.delay(
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        config_key="text_generation",
        prompt=prompt,
    )

    return RegenerateResponse(task_id=task.id)


@router.get("/styles", response_model=StylesResponse)
async def get_available_styles():
    """Get list of available image generation styles."""
    styles = [
        ImageStyle(
            id="realistic",
            name="写实风格",
            description="真实感强的照片级图片",
        ),
        ImageStyle(
            id="illustration",
            name="插画风格",
            description="温暖手绘插画风格",
        ),
        ImageStyle(
            id="flat",
            name="扁平化",
            description="现代简洁的扁平设计风格",
        ),
        ImageStyle(
            id="watercolor",
            name="水彩风格",
            description="柔和梦幻的水彩画风格",
        ),
        ImageStyle(
            id="anime",
            name="动漫风格",
            description="日系动漫插画风格",
        ),
    ]
    return StylesResponse(styles=styles)
