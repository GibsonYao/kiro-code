"""Points service layer — business logic for points accounts and transactions.

Provides functions to manage points accounts and record transactions
when tasks/actions are approved or penalties are applied.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.points import PointsAccount, PointsTransaction, PointsTransactionType
from app.models.user import User


async def get_or_create_account(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
) -> PointsAccount:
    """Get an existing points account or create a new one.

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID.

    Returns:
        The PointsAccount instance.
    """
    query = select(PointsAccount).where(
        PointsAccount.family_id == family_id,
        PointsAccount.user_id == user_id,
    )
    result = await db.execute(query)
    account = result.scalar_one_or_none()

    if account is None:
        account = PointsAccount(
            family_id=family_id,
            user_id=user_id,
            balance=0,
            total_earned=0,
            total_spent=0,
        )
        db.add(account)
        await db.flush()
        await db.refresh(account)

    return account


async def award_points(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
    amount: int,
    source_type: str,
    source_id: uuid.UUID,
    description: str,
) -> PointsTransaction:
    """Award points to a user and record the transaction.

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID.
        amount: Points to award (positive integer).
        source_type: Type of source entity (e.g., "task", "action").
        source_id: UUID of the source entity.
        description: Human-readable description of the transaction.

    Returns:
        The created PointsTransaction instance.
    """
    account = await get_or_create_account(db, family_id, user_id)

    account.balance += amount
    account.total_earned += amount

    transaction = PointsTransaction(
        account_id=account.id,
        type=PointsTransactionType.reward,
        amount=amount,
        balance_after=account.balance,
        source_type=source_type,
        source_id=source_id,
        description=description,
    )
    db.add(transaction)
    await db.flush()
    await db.refresh(transaction)

    return transaction


async def deduct_points(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
    amount: int,
    source_type: str,
    source_id: uuid.UUID,
    description: str,
) -> PointsTransaction:
    """Deduct points from a user and record the transaction.

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID.
        amount: Points to deduct (positive integer, will be stored as negative).
        source_type: Type of source entity (e.g., "task").
        source_id: UUID of the source entity.
        description: Human-readable description of the transaction.

    Returns:
        The created PointsTransaction instance.
    """
    account = await get_or_create_account(db, family_id, user_id)

    account.balance -= amount
    account.total_spent += amount

    transaction = PointsTransaction(
        account_id=account.id,
        type=PointsTransactionType.penalty,
        amount=-amount,
        balance_after=account.balance,
        source_type=source_type,
        source_id=source_id,
        description=description,
    )
    db.add(transaction)
    await db.flush()
    await db.refresh(transaction)

    return transaction


async def get_points_history(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
    type_filter: PointsTransactionType | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[PointsTransaction], int]:
    """Get paginated points transaction history for a user.

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID.
        type_filter: Optional filter by transaction type.
        page: Page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        Tuple of (list of transactions, total count).
    """
    # First get the account
    account_query = select(PointsAccount.id).where(
        PointsAccount.family_id == family_id,
        PointsAccount.user_id == user_id,
    )
    account_result = await db.execute(account_query)
    account_id = account_result.scalar_one_or_none()

    if account_id is None:
        return [], 0

    # Build base query for transactions
    base_filter = [PointsTransaction.account_id == account_id]
    if type_filter is not None:
        base_filter.append(PointsTransaction.type == type_filter)

    # Count total
    count_query = select(func.count()).select_from(PointsTransaction).where(*base_filter)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Fetch paginated results
    offset = (page - 1) * page_size
    items_query = (
        select(PointsTransaction)
        .where(*base_filter)
        .order_by(PointsTransaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items_result = await db.execute(items_query)
    items = list(items_result.scalars().all())

    return items, total


async def get_leaderboard(
    db: AsyncSession,
    family_id: uuid.UUID,
) -> list[dict]:
    """Get the points leaderboard for a family.

    Returns family members ranked by total_earned descending,
    joined with User to get nicknames.

    Args:
        db: Database session.
        family_id: Family UUID.

    Returns:
        List of dicts with user_id, nickname, balance, total_earned.
    """
    query = (
        select(
            PointsAccount.user_id,
            User.nickname,
            PointsAccount.balance,
            PointsAccount.total_earned,
        )
        .join(User, PointsAccount.user_id == User.id)
        .where(PointsAccount.family_id == family_id)
        .order_by(PointsAccount.total_earned.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "user_id": row.user_id,
            "nickname": row.nickname,
            "balance": row.balance,
            "total_earned": row.total_earned,
        }
        for row in rows
    ]
