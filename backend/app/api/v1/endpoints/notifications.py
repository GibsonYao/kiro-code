"""Notification API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_family, get_current_user, get_db
from app.models.notification import NotificationType
from app.schemas.notification import NotificationListOut, NotificationOut, UnreadCountOut
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=NotificationListOut)
async def list_notifications(
    type: NotificationType | None = Query(None, description="Filter by notification type"),
    current_user=Depends(get_current_user),
    family=Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get notification list with unread count."""
    service = NotificationService(db)
    notifications = await service.get_notifications(
        user_id=current_user.id,
        family_id=family.family_id,
        notification_type=type,
    )
    unread_count = await service.get_unread_count(
        user_id=current_user.id,
        family_id=family.family_id,
    )
    return NotificationListOut(
        items=[NotificationOut.model_validate(n) for n in notifications],
        unread_count=unread_count,
    )


@router.get("/unread-count", response_model=UnreadCountOut)
async def get_unread_count(
    current_user=Depends(get_current_user),
    family=Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get unread notification count (for badge display)."""
    service = NotificationService(db)
    count = await service.get_unread_count(
        user_id=current_user.id,
        family_id=family.family_id,
    )
    return UnreadCountOut(unread_count=count)


@router.post("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a single notification as read."""
    service = NotificationService(db)
    success = await service.mark_as_read(notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="通知不存在")
    return {"message": "已标记为已读"}


@router.post("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_read(
    current_user=Depends(get_current_user),
    family=Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read."""
    service = NotificationService(db)
    count = await service.mark_all_as_read(current_user.id, family.family_id)
    return {"message": f"已标记{count}条通知为已读"}
