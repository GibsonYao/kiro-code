"""AI generation status API endpoints."""

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.tasks import celery_app

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
