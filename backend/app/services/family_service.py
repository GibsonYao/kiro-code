"""Family service layer — business logic for family management."""

import secrets
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.family import Family, FamilyAppellation, FamilyMember, FamilyRole
from app.models.user import User


async def create_family(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    avatar_url: str | None = None,
) -> tuple[Family, FamilyMember]:
    """Create a new family and add the creator as admin.

    Args:
        db: Database session.
        user_id: Creator's user UUID.
        name: Family name.
        avatar_url: Optional family avatar URL.

    Returns:
        Tuple of (Family, FamilyMember) for the creator.
    """
    invite_code = secrets.token_hex(6)

    family = Family(
        name=name,
        avatar_url=avatar_url,
        invite_code=invite_code,
        created_by=user_id,
    )
    db.add(family)
    await db.flush()
    await db.refresh(family)

    # Add creator as admin member
    membership = FamilyMember(
        family_id=family.id,
        user_id=user_id,
        role=FamilyRole.admin,
        nickname_in_family=None,
    )
    db.add(membership)
    await db.flush()
    await db.refresh(membership)

    return family, membership


async def get_family_by_id(
    db: AsyncSession,
    family_id: uuid.UUID,
) -> Family | None:
    """Get a family by ID.

    Args:
        db: Database session.
        family_id: Family UUID.

    Returns:
        Family instance or None.
    """
    query = select(Family).where(Family.id == family_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_family_by_invite_code(
    db: AsyncSession,
    invite_code: str,
) -> Family | None:
    """Get a family by invite code.

    Args:
        db: Database session.
        invite_code: The family's invite code.

    Returns:
        Family instance or None.
    """
    query = select(Family).where(Family.invite_code == invite_code)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def join_family(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
    nickname_in_family: str | None = None,
    relationship: str | None = None,
) -> FamilyMember:
    """Join an existing family.

    Args:
        db: Database session.
        family_id: Family UUID to join.
        user_id: User UUID.
        nickname_in_family: Optional nickname within the family.
        relationship: Optional relationship description.

    Returns:
        Created FamilyMember instance.

    Raises:
        ValueError: If user is already a member of this family.
    """
    # Check if already a member
    existing = await get_membership(db, family_id, user_id)
    if existing is not None:
        raise ValueError("该成员已在此家庭中")

    membership = FamilyMember(
        family_id=family_id,
        user_id=user_id,
        role=FamilyRole.member,
        nickname_in_family=nickname_in_family,
        relationship=relationship,
    )
    db.add(membership)
    await db.flush()
    await db.refresh(membership)
    return membership


async def get_membership(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
) -> FamilyMember | None:
    """Get a user's membership in a specific family.

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID.

    Returns:
        FamilyMember instance or None.
    """
    query = select(FamilyMember).where(
        FamilyMember.family_id == family_id,
        FamilyMember.user_id == user_id,
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_family_members(
    db: AsyncSession,
    family_id: uuid.UUID,
) -> list[tuple[FamilyMember, User]]:
    """Get all members of a family with their user info.

    Args:
        db: Database session.
        family_id: Family UUID.

    Returns:
        List of (FamilyMember, User) tuples.
    """
    query = (
        select(FamilyMember, User)
        .join(User, FamilyMember.user_id == User.id)
        .where(FamilyMember.family_id == family_id)
        .order_by(FamilyMember.created_at.asc())
    )
    result = await db.execute(query)
    return list(result.all())


async def add_family_member(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
    role: FamilyRole = FamilyRole.member,
    nickname_in_family: str | None = None,
    relationship: str | None = None,
) -> FamilyMember:
    """Add a member to a family (admin operation).

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID to add.
        role: Member role.
        nickname_in_family: Optional nickname.
        relationship: Optional relationship.

    Returns:
        Created FamilyMember instance.

    Raises:
        ValueError: If user is already a member.
    """
    existing = await get_membership(db, family_id, user_id)
    if existing is not None:
        raise ValueError("该成员已在此家庭中")

    membership = FamilyMember(
        family_id=family_id,
        user_id=user_id,
        role=role,
        nickname_in_family=nickname_in_family,
        relationship=relationship,
    )
    db.add(membership)
    await db.flush()
    await db.refresh(membership)
    return membership


async def remove_family_member(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Remove a member from a family.

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID to remove.

    Raises:
        ValueError: If user is not a member.
    """
    membership = await get_membership(db, family_id, user_id)
    if membership is None:
        raise ValueError("该成员不在此家庭中")

    # Also remove related appellations
    appellation_query = select(FamilyAppellation).where(
        FamilyAppellation.family_id == family_id,
        (FamilyAppellation.from_member_id == membership.id)
        | (FamilyAppellation.to_member_id == membership.id),
    )
    result = await db.execute(appellation_query)
    appellations = result.scalars().all()
    for app in appellations:
        await db.delete(app)

    await db.delete(membership)
    await db.flush()


async def set_appellation(
    db: AsyncSession,
    family_id: uuid.UUID,
    from_member_id: uuid.UUID,
    to_member_id: uuid.UUID,
    appellation: str,
) -> FamilyAppellation:
    """Set or update the appellation between two family members.

    Args:
        db: Database session.
        family_id: Family UUID.
        from_member_id: FamilyMember ID of the viewer.
        to_member_id: FamilyMember ID of the person being addressed.
        appellation: The appellation string (e.g., "爸爸", "妹妹").

    Returns:
        Created or updated FamilyAppellation instance.
    """
    query = select(FamilyAppellation).where(
        FamilyAppellation.family_id == family_id,
        FamilyAppellation.from_member_id == from_member_id,
        FamilyAppellation.to_member_id == to_member_id,
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing is not None:
        existing.appellation = appellation
        await db.flush()
        await db.refresh(existing)
        return existing

    new_appellation = FamilyAppellation(
        family_id=family_id,
        from_member_id=from_member_id,
        to_member_id=to_member_id,
        appellation=appellation,
    )
    db.add(new_appellation)
    await db.flush()
    await db.refresh(new_appellation)
    return new_appellation


async def get_appellations_for_member(
    db: AsyncSession,
    family_id: uuid.UUID,
    from_member_id: uuid.UUID,
) -> list[FamilyAppellation]:
    """Get all appellations from a member's perspective.

    Args:
        db: Database session.
        family_id: Family UUID.
        from_member_id: FamilyMember ID of the viewer.

    Returns:
        List of FamilyAppellation instances.
    """
    query = select(FamilyAppellation).where(
        FamilyAppellation.family_id == family_id,
        FamilyAppellation.from_member_id == from_member_id,
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_user_families(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[tuple[FamilyMember, Family]]:
    """Get all families a user belongs to.

    Args:
        db: Database session.
        user_id: User UUID.

    Returns:
        List of (FamilyMember, Family) tuples.
    """
    query = (
        select(FamilyMember, Family)
        .join(Family, FamilyMember.family_id == Family.id)
        .where(FamilyMember.user_id == user_id)
        .order_by(FamilyMember.created_at.asc())
    )
    result = await db.execute(query)
    return list(result.all())
