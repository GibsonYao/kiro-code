"""Points-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.points import PointsTransactionType


# ─── Response Schemas ──────────────────────────────────────────────────────────


class PointsBalanceResponse(BaseModel):
    """Response containing the user's points balance."""

    balance: int
    total_earned: int
    total_spent: int

    model_config = {"from_attributes": True}


class PointsTransactionResponse(BaseModel):
    """Response containing a single points transaction."""

    id: uuid.UUID
    type: PointsTransactionType
    amount: int
    balance_after: int
    source_type: str | None = None
    source_id: uuid.UUID | None = None
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PointsHistoryResponse(BaseModel):
    """Paginated list of points transactions."""

    items: list[PointsTransactionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class PointsLeaderboardEntry(BaseModel):
    """A single entry in the points leaderboard."""

    user_id: uuid.UUID
    nickname: str | None = None
    balance: int
    total_earned: int

    model_config = {"from_attributes": True}


class PointsLeaderboardResponse(BaseModel):
    """Response containing the family points leaderboard."""

    items: list[PointsLeaderboardEntry]
