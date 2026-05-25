"""Points API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_family, get_current_user, get_db
from app.models.family import FamilyMember
from app.models.points import PointsTransactionType
from app.models.user import User
from app.schemas.points import (
    PointsBalanceResponse,
    PointsHistoryResponse,
    PointsLeaderboardEntry,
    PointsLeaderboardResponse,
    PointsTransactionResponse,
)
from app.services.points_service import (
    get_leaderboard,
    get_or_create_account,
    get_points_history,
)

router = APIRouter()


@router.get("/balance", response_model=PointsBalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's points balance."""
    account = await get_or_create_account(
        db=db,
        family_id=membership.family_id,
        user_id=current_user.id,
    )
    return PointsBalanceResponse(
        balance=account.balance,
        total_earned=account.total_earned,
        total_spent=account.total_spent,
    )


@router.get("/history", response_model=PointsHistoryResponse)
async def get_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    type: PointsTransactionType | None = Query(None, description="交易类型筛选"),
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated points transaction history with optional type filter."""
    items, total = await get_points_history(
        db=db,
        family_id=membership.family_id,
        user_id=current_user.id,
        type_filter=type,
        page=page,
        page_size=page_size,
    )

    return PointsHistoryResponse(
        items=[PointsTransactionResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/leaderboard", response_model=PointsLeaderboardResponse)
async def get_leaderboard_endpoint(
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get the family points leaderboard ranked by total_earned."""
    entries = await get_leaderboard(
        db=db,
        family_id=membership.family_id,
    )

    return PointsLeaderboardResponse(
        items=[PointsLeaderboardEntry(**entry) for entry in entries],
    )
