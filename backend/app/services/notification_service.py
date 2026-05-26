"""Unified notification service.

Handles in-app notifications, WeChat subscription messages (stub),
and Web Push (stub with fallback to in-app).
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationCreate

logger = logging.getLogger(__name__)


class NotificationService:
    """Unified notification service that routes to appropriate channels."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_notification(self, data: NotificationCreate) -> Notification:
        """Send a notification through the appropriate channel.

        Currently creates an in-app notification. WeChat and Web Push
        are logged as stubs for future implementation.
        """
        # Always create in-app notification
        notification = await self._create_in_app_notification(data)

        # Attempt WeChat subscription message (stub)
        self._send_wechat_subscription(data)

        # Attempt Web Push (stub, falls back to in-app)
        self._send_web_push(data)

        return notification

    async def _create_in_app_notification(self, data: NotificationCreate) -> Notification:
        """Create an in-app notification record."""
        notification = Notification(
            user_id=data.user_id,
            family_id=data.family_id,
            type=data.type,
            title=data.title,
            content=data.content,
            target_type=data.target_type,
            target_id=data.target_id,
            is_read=False,
        )
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        return notification

    def _send_wechat_subscription(self, data: NotificationCreate) -> None:
        """Send WeChat subscription message (stub).

        Templates:
        - task_remind: 任务提醒模板
        - review: 审核通知模板
        - points: 积分变动模板
        - anniversary: 纪念日提醒模板
        """
        template_map = {
            NotificationType.task_remind: "TASK_REMIND_TEMPLATE_ID",
            NotificationType.review: "REVIEW_NOTIFY_TEMPLATE_ID",
            NotificationType.points: "POINTS_CHANGE_TEMPLATE_ID",
            NotificationType.anniversary: "ANNIVERSARY_REMIND_TEMPLATE_ID",
        }
        template_id = template_map.get(data.type)
        if template_id:
            logger.info(
                f"[WeChat Push Stub] Would send template '{template_id}' "
                f"to user {data.user_id}: {data.title}"
            )

    def _send_web_push(self, data: NotificationCreate) -> None:
        """Send Web Push notification via Service Worker (stub).

        Falls back to in-app notification (already created).
        """
        logger.info(
            f"[Web Push Stub] Would send push to user {data.user_id}: "
            f"{data.title} - falling back to in-app notification"
        )

    async def get_notifications(
        self,
        user_id: uuid.UUID,
        family_id: uuid.UUID,
        notification_type: NotificationType | None = None,
        limit: int = 50,
    ) -> list[Notification]:
        """Get notifications for a user."""
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.family_id == family_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        if notification_type:
            stmt = stmt.where(Notification.type == notification_type)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: uuid.UUID, family_id: uuid.UUID) -> int:
        """Get unread notification count."""
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.family_id == family_id)
            .where(Notification.is_read == False)  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Mark a single notification as read."""
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .where(Notification.user_id == user_id)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0  # type: ignore

    async def mark_all_as_read(self, user_id: uuid.UUID, family_id: uuid.UUID) -> int:
        """Mark all notifications as read for a user."""
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.family_id == family_id)
            .where(Notification.is_read == False)  # noqa: E712
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        result = await self.db.execute(stmt)
        return result.rowcount  # type: ignore
