"""Cascade unlink API endpoints — check and unlink downstream items."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.services.cascade_unlink_service import (
    VALID_ENTITY_TYPES,
    check_downstream_links,
    unlink_downstream,
)

router = APIRouter()


class DownstreamLinksResponse(BaseModel):
    """Response model for downstream links check."""

    entity_type: str
    entity_id: str
    downstream: dict[str, int]
    has_downstream: bool


class UnlinkResponse(BaseModel):
    """Response model for unlink operation."""

    entity_type: str
    entity_id: str
    unlinked: bool


@router.get(
    "/{entity_type}/{entity_id}/downstream-links",
    response_model=DownstreamLinksResponse,
)
async def get_downstream_links(
    entity_type: str,
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Get counts of downstream items linked to the specified entity.

    This endpoint is used by the frontend to show a confirmation dialog
    before deleting an entity that has downstream links.

    Args:
        entity_type: Type of entity (wish, goal, plan, task).
        entity_id: UUID of the entity.

    Returns:
        DownstreamLinksResponse with counts and whether any downstream items exist.
    """
    if entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的实体类型: {entity_type}。有效类型: {', '.join(VALID_ENTITY_TYPES)}",
        )

    downstream = await check_downstream_links(db, entity_type, entity_id)
    has_downstream = any(count > 0 for count in downstream.values())

    return DownstreamLinksResponse(
        entity_type=entity_type,
        entity_id=str(entity_id),
        downstream=downstream,
        has_downstream=has_downstream,
    )


@router.post(
    "/{entity_type}/{entity_id}/unlink-downstream",
    response_model=UnlinkResponse,
)
async def post_unlink_downstream(
    entity_type: str,
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),
):
    """Unlink all downstream items from the specified entity.

    Sets downstream foreign keys to NULL so the entity can be safely deleted
    without losing the downstream items.

    Args:
        entity_type: Type of entity (wish, goal, plan, task).
        entity_id: UUID of the entity.

    Returns:
        UnlinkResponse confirming the operation.
    """
    if entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的实体类型: {entity_type}。有效类型: {', '.join(VALID_ENTITY_TYPES)}",
        )

    await unlink_downstream(db, entity_type, entity_id)

    return UnlinkResponse(
        entity_type=entity_type,
        entity_id=str(entity_id),
        unlinked=True,
    )
