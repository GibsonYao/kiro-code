"""Family management API endpoints (Task 18)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_family, get_current_user, get_db
from app.models.family import FamilyMember, FamilyRole
from app.models.user import User
from app.services.family_service import (
    add_family_member,
    create_family,
    get_appellations_for_member,
    get_family_by_invite_code,
    get_family_members,
    get_membership,
    get_user_families,
    remove_family_member,
    set_appellation,
)

router = APIRouter()


# ─── Request/Response Schemas ──────────────────────────────────────────────────


class CreateFamilyRequest(BaseModel):
    """Request body for creating a family."""

    name: str = Field(..., min_length=1, max_length=128, description="家庭名称")
    avatar_url: str | None = Field(None, description="家庭头像URL")


class JoinFamilyRequest(BaseModel):
    """Request body for joining a family via invite code."""

    invite_code: str = Field(..., min_length=1, description="邀请码")
    nickname_in_family: str | None = Field(None, description="在家庭中的昵称")
    relationship: str | None = Field(None, description="关系描述")


class AddMemberRequest(BaseModel):
    """Request body for adding a member to the family."""

    user_id: uuid.UUID = Field(..., description="要添加的用户ID")
    nickname_in_family: str | None = Field(None, description="在家庭中的昵称")
    relationship: str | None = Field(None, description="关系描述")


class SetAppellationRequest(BaseModel):
    """Request body for setting an appellation."""

    appellation: str = Field(..., min_length=1, max_length=64, description="称谓（如：爸爸、妹妹）")


class SwitchFamilyRequest(BaseModel):
    """Request body for switching family context."""

    family_id: uuid.UUID = Field(..., description="要切换到的家庭ID")


class FamilyResponse(BaseModel):
    """Response containing family information."""

    id: uuid.UUID
    name: str
    avatar_url: str | None = None
    invite_code: str
    created_by: uuid.UUID

    model_config = {"from_attributes": True}


class FamilyMemberResponse(BaseModel):
    """Response containing family member information."""

    id: uuid.UUID
    family_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    nickname_in_family: str | None = None
    relationship: str | None = None
    # User info
    user_nickname: str | None = None
    user_avatar_url: str | None = None
    # Appellation from current user's perspective
    appellation: str | None = None


class FamilyMemberListResponse(BaseModel):
    """Response containing list of family members."""

    items: list[FamilyMemberResponse]
    total: int


class AppellationResponse(BaseModel):
    """Response for appellation setting."""

    from_member_id: uuid.UUID
    to_member_id: uuid.UUID
    appellation: str

    model_config = {"from_attributes": True}


class UserFamilyItem(BaseModel):
    """A family the user belongs to."""

    family_id: uuid.UUID
    family_name: str
    role: str
    is_current: bool = False


class UserFamiliesResponse(BaseModel):
    """List of families the user belongs to."""

    items: list[UserFamilyItem]


# ─── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def create_family_endpoint(
    body: CreateFamilyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new family. The creator becomes the family admin."""
    family, _ = await create_family(
        db=db,
        user_id=current_user.id,
        name=body.name,
        avatar_url=body.avatar_url,
    )
    return FamilyResponse.model_validate(family)


@router.get("/current", response_model=FamilyResponse)
async def get_current_family_info(
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's active family information."""
    from app.services.family_service import get_family_by_id

    family = await get_family_by_id(db=db, family_id=membership.family_id)
    if family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="家庭不存在",
        )
    return FamilyResponse.model_validate(family)


@router.post("/join", response_model=FamilyMemberResponse)
async def join_family_endpoint(
    body: JoinFamilyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a family using an invite code."""
    family = await get_family_by_invite_code(db=db, invite_code=body.invite_code)
    if family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邀请码无效",
        )

    # Check if already a member
    existing = await get_membership(db=db, family_id=family.id, user_id=current_user.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="您已是该家庭成员",
        )

    membership = await add_family_member(
        db=db,
        family_id=family.id,
        user_id=current_user.id,
        nickname_in_family=body.nickname_in_family,
        relationship=body.relationship,
    )

    return FamilyMemberResponse(
        id=membership.id,
        family_id=membership.family_id,
        user_id=membership.user_id,
        role=membership.role.value,
        nickname_in_family=membership.nickname_in_family,
        relationship=membership.relationship,
        user_nickname=current_user.nickname,
        user_avatar_url=current_user.avatar_url,
    )


@router.get("/members", response_model=FamilyMemberListResponse)
async def list_family_members(
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get all members of the current family with appellations from current user's perspective."""
    members_with_users = await get_family_members(db=db, family_id=membership.family_id)

    # Get appellations from current user's perspective
    appellations = await get_appellations_for_member(
        db=db,
        family_id=membership.family_id,
        from_member_id=membership.id,
    )
    appellation_map = {a.to_member_id: a.appellation for a in appellations}

    items = []
    for member, user in members_with_users:
        items.append(
            FamilyMemberResponse(
                id=member.id,
                family_id=member.family_id,
                user_id=member.user_id,
                role=member.role.value if hasattr(member.role, "value") else str(member.role),
                nickname_in_family=member.nickname_in_family,
                relationship=member.relationship,
                user_nickname=user.nickname,
                user_avatar_url=user.avatar_url,
                appellation=appellation_map.get(member.id),
            )
        )

    return FamilyMemberListResponse(items=items, total=len(items))


@router.post("/members", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member_endpoint(
    body: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Add a member to the family. Only family admin can add members."""
    if membership.role != FamilyRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有家庭管理员可以添加成员",
        )

    try:
        new_member = await add_family_member(
            db=db,
            family_id=membership.family_id,
            user_id=body.user_id,
            nickname_in_family=body.nickname_in_family,
            relationship=body.relationship,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    return FamilyMemberResponse(
        id=new_member.id,
        family_id=new_member.family_id,
        user_id=new_member.user_id,
        role=new_member.role.value,
        nickname_in_family=new_member.nickname_in_family,
        relationship=new_member.relationship,
    )


@router.delete("/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_endpoint(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the family. Only family admin can remove members."""
    if membership.role != FamilyRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有家庭管理员可以移除成员",
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能移除自己",
        )

    try:
        await remove_family_member(db=db, family_id=membership.family_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put("/members/{member_id}/appellation", response_model=AppellationResponse)
async def set_member_appellation(
    member_id: uuid.UUID,
    body: SetAppellationRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Set the appellation for a family member from the current user's perspective."""
    appellation = await set_appellation(
        db=db,
        family_id=membership.family_id,
        from_member_id=membership.id,
        to_member_id=member_id,
        appellation=body.appellation,
    )
    return AppellationResponse.model_validate(appellation)


@router.put("/switch/{family_id}", response_model=FamilyResponse)
async def switch_family(
    family_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Switch the current user's active family context.

    Verifies the user is a member of the target family.
    """
    from app.services.family_service import get_family_by_id

    # Verify membership
    target_membership = await get_membership(db=db, family_id=family_id, user_id=current_user.id)
    if target_membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该家庭的成员",
        )

    family = await get_family_by_id(db=db, family_id=family_id)
    if family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="家庭不存在",
        )

    return FamilyResponse.model_validate(family)


@router.get("/my-families", response_model=UserFamiliesResponse)
async def list_user_families(
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get all families the current user belongs to."""
    families = await get_user_families(db=db, user_id=current_user.id)

    items = []
    for member, family in families:
        items.append(
            UserFamilyItem(
                family_id=family.id,
                family_name=family.name,
                role=member.role.value if hasattr(member.role, "value") else str(member.role),
                is_current=(family.id == membership.family_id),
            )
        )

    return UserFamiliesResponse(items=items)
