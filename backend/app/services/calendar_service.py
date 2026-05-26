"""Calendar service layer — business logic for calendar event CRUD."""

import uuid
from datetime import date, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action, ActionStatus, ActionType
from app.models.calendar import CalendarEvent, CalendarEventType


async def get_calendar_events(
    db: AsyncSession,
    family_id: uuid.UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    event_type: CalendarEventType | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[CalendarEvent], int]:
    """Get paginated list of calendar events for a family.

    Args:
        db: Database session.
        family_id: Family UUID to filter by.
        start_date: Optional start date for range filtering.
        end_date: Optional end date for range filtering.
        event_type: Optional event type filter.
        page: Page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        Tuple of (events list, total count).
    """
    base_query = select(CalendarEvent).where(CalendarEvent.family_id == family_id)

    if start_date is not None:
        base_query = base_query.where(CalendarEvent.event_date >= start_date)
    if end_date is not None:
        base_query = base_query.where(CalendarEvent.event_date <= end_date)
    if event_type is not None:
        base_query = base_query.where(CalendarEvent.event_type == event_type)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results
    offset = (page - 1) * page_size
    query = base_query.order_by(CalendarEvent.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    events = list(result.scalars().all())

    return events, total


async def get_calendar_event_by_id(
    db: AsyncSession,
    event_id: uuid.UUID,
    family_id: uuid.UUID,
) -> CalendarEvent | None:
    """Get a single calendar event by ID, scoped to a family.

    Args:
        db: Database session.
        event_id: Event UUID.
        family_id: Family UUID for access control.

    Returns:
        CalendarEvent instance or None if not found.
    """
    query = select(CalendarEvent).where(
        CalendarEvent.id == event_id, CalendarEvent.family_id == family_id
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_calendar_event(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
    event_type: CalendarEventType,
    event_date: date | None = None,
    event_time: time | None = None,
    is_recurring: bool = False,
    remind_before_days: int = 0,
    sync_to_action: bool = True,
) -> CalendarEvent:
    """Create a new calendar event.

    When event_type is 'schedule', automatically creates a corresponding
    Action of type 'schedule' in the actions module (Task 16.3).

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID (event creator).
        title: Event title.
        event_type: Event type (schedule/todo/anniversary).
        event_date: Event date (optional).
        event_time: Event time (optional).
        is_recurring: Whether the event is recurring.
        remind_before_days: Days before event to send reminder.
        sync_to_action: Whether to sync schedule events to actions module.

    Returns:
        Created CalendarEvent instance.
    """
    event = CalendarEvent(
        family_id=family_id,
        user_id=user_id,
        title=title,
        event_type=event_type,
        event_date=event_date,
        event_time=event_time,
        is_recurring=is_recurring,
        remind_before_days=remind_before_days,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)

    # Task 16.3: Auto-sync schedule events to the actions module
    if sync_to_action and event_type == CalendarEventType.schedule:
        action = Action(
            family_id=family_id,
            user_id=user_id,
            title=title,
            action_type=ActionType.schedule,
            scheduled_date=event_date,
            scheduled_time=event_time,
            status=ActionStatus.pending,
        )
        db.add(action)
        await db.flush()
        await db.refresh(action)

        # Link the calendar event to the action
        event.action_id = action.id
        await db.flush()
        await db.refresh(event)

    return event


async def update_calendar_event(
    db: AsyncSession,
    event: CalendarEvent,
    title: str | None = None,
    event_type: CalendarEventType | None = None,
    event_date: date | None = None,
    event_time: time | None = None,
    is_recurring: bool | None = None,
    remind_before_days: int | None = None,
) -> CalendarEvent:
    """Update an existing calendar event.

    Args:
        db: Database session.
        event: CalendarEvent instance to update.
        title: New title (optional).
        event_type: New event type (optional).
        event_date: New event date (optional).
        event_time: New event time (optional).
        is_recurring: New recurring flag (optional).
        remind_before_days: New remind days (optional).

    Returns:
        Updated CalendarEvent instance.
    """
    if title is not None:
        event.title = title
    if event_type is not None:
        event.event_type = event_type
    if event_date is not None:
        event.event_date = event_date
    if event_time is not None:
        event.event_time = event_time
    if is_recurring is not None:
        event.is_recurring = is_recurring
    if remind_before_days is not None:
        event.remind_before_days = remind_before_days

    await db.flush()
    await db.refresh(event)
    return event


async def delete_calendar_event(db: AsyncSession, event: CalendarEvent) -> None:
    """Delete a calendar event.

    Args:
        db: Database session.
        event: CalendarEvent instance to delete.
    """
    await db.delete(event)
    await db.flush()


# ─── Anniversary-specific functions (Task 16.2) ───────────────────────────────


async def get_anniversaries(
    db: AsyncSession,
    family_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[CalendarEvent], int]:
    """Get paginated list of anniversary events for a family.

    Args:
        db: Database session.
        family_id: Family UUID.
        page: Page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        Tuple of (anniversaries list, total count).
    """
    base_query = select(CalendarEvent).where(
        CalendarEvent.family_id == family_id,
        CalendarEvent.event_type == CalendarEventType.anniversary,
    )

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results
    offset = (page - 1) * page_size
    query = base_query.order_by(CalendarEvent.event_date.asc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    events = list(result.scalars().all())

    return events, total


async def get_upcoming_anniversaries(
    db: AsyncSession,
    family_id: uuid.UUID,
    within_days: int = 30,
) -> list[CalendarEvent]:
    """Get anniversaries coming up within the specified number of days.

    Used by the reminder Celery Beat task to send notifications.

    Args:
        db: Database session.
        family_id: Family UUID.
        within_days: Number of days to look ahead.

    Returns:
        List of upcoming anniversary events.
    """
    from datetime import timedelta

    today = date.today()
    end_date = today + timedelta(days=within_days)

    # For recurring anniversaries, we need to check month/day regardless of year
    # Simple approach: get all anniversaries and filter in Python
    query = select(CalendarEvent).where(
        CalendarEvent.family_id == family_id,
        CalendarEvent.event_type == CalendarEventType.anniversary,
    )
    result = await db.execute(query)
    all_anniversaries = list(result.scalars().all())

    upcoming = []
    for ann in all_anniversaries:
        if ann.event_date is None:
            continue
        # Check if the anniversary date (month/day) falls within the window
        try:
            this_year_date = ann.event_date.replace(year=today.year)
        except ValueError:
            # Handle Feb 29 in non-leap years
            this_year_date = ann.event_date.replace(year=today.year, day=28)

        if this_year_date < today:
            # Check next year
            try:
                this_year_date = ann.event_date.replace(year=today.year + 1)
            except ValueError:
                this_year_date = ann.event_date.replace(year=today.year + 1, day=28)

        if today <= this_year_date <= end_date:
            upcoming.append(ann)

    return upcoming
