"""Calendar events API endpoints."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_family, get_current_user, get_db
from app.models.calendar import CalendarEventType
from app.models.family import FamilyMember
from app.models.user import User
from app.schemas.calendar import (
    AnniversaryCreateRequest,
    AnniversaryListResponse,
    CalendarEventCreateRequest,
    CalendarEventListResponse,
    CalendarEventResponse,
    CalendarEventUpdateRequest,
)
from app.services.calendar_service import (
    create_calendar_event,
    delete_calendar_event,
    get_anniversaries,
    get_calendar_event_by_id,
    get_calendar_events,
    update_calendar_event,
)

router = APIRouter()


@router.get("/events", response_model=CalendarEventListResponse)
async def list_calendar_events(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    start_date: date | None = Query(None, description="开始日期（含）"),
    end_date: date | None = Query(None, description="结束日期（含）"),
    event_type: CalendarEventType | None = Query(None, description="事件类型筛选"),
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of calendar events with optional date range filtering."""
    events, total = await get_calendar_events(
        db=db,
        family_id=membership.family_id,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        page=page,
        page_size=page_size,
    )

    return CalendarEventListResponse(
        items=[CalendarEventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_event_endpoint(
    body: CalendarEventCreateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Create a new calendar event."""
    event = await create_calendar_event(
        db=db,
        family_id=membership.family_id,
        user_id=current_user.id,
        title=body.title,
        event_type=body.event_type,
        event_date=body.event_date,
        event_time=body.event_time,
        is_recurring=body.is_recurring,
        remind_before_days=body.remind_before_days,
    )

    return CalendarEventResponse.model_validate(event)


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_calendar_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get a single calendar event by ID."""
    event = await get_calendar_event_by_id(db=db, event_id=event_id, family_id=membership.family_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日历事件不存在",
        )
    return CalendarEventResponse.model_validate(event)


@router.put("/events/{event_id}", response_model=CalendarEventResponse)
async def update_calendar_event_endpoint(
    event_id: uuid.UUID,
    body: CalendarEventUpdateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Update a calendar event. Only the creator or family admin can update."""
    event = await get_calendar_event_by_id(db=db, event_id=event_id, family_id=membership.family_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日历事件不存在",
        )

    # Only the event creator or family admin can update
    if event.user_id != current_user.id and membership.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有事件创建者或家庭管理员可以修改日历事件",
        )

    event = await update_calendar_event(
        db=db,
        event=event,
        title=body.title,
        event_type=body.event_type,
        event_date=body.event_date,
        event_time=body.event_time,
        is_recurring=body.is_recurring,
        remind_before_days=body.remind_before_days,
    )

    return CalendarEventResponse.model_validate(event)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar_event_endpoint(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Delete a calendar event. Only the creator or family admin can delete."""
    event = await get_calendar_event_by_id(db=db, event_id=event_id, family_id=membership.family_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="日历事件不存在",
        )

    # Only the event creator or family admin can delete
    if event.user_id != current_user.id and membership.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有事件创建者或家庭管理员可以删除日历事件",
        )

    await delete_calendar_event(db=db, event=event)


# ─── Anniversary Endpoints (Task 16.2) ────────────────────────────────────────


@router.get("/anniversaries", response_model=AnniversaryListResponse)
async def list_anniversaries(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of family anniversaries."""
    events, total = await get_anniversaries(
        db=db,
        family_id=membership.family_id,
        page=page,
        page_size=page_size,
    )

    return AnniversaryListResponse(
        items=[CalendarEventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("/anniversaries", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_anniversary(
    body: AnniversaryCreateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Create a new family anniversary (birthday, wedding anniversary, etc.)."""
    event = await create_calendar_event(
        db=db,
        family_id=membership.family_id,
        user_id=current_user.id,
        title=body.title,
        event_type=CalendarEventType.anniversary,
        event_date=body.event_date,
        is_recurring=True,  # Anniversaries are always recurring
        remind_before_days=body.remind_before_days,
        sync_to_action=False,  # Anniversaries don't sync to actions
    )

    return CalendarEventResponse.model_validate(event)
