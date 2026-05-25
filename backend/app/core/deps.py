"""Dependency injection utilities."""

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import verify_access_token

# Async engine configured with the DATABASE_URL from settings
_engine_kwargs: dict = {
    "echo": settings.DEBUG,
}
# SQLite doesn't support connection pooling options
if not settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(pool_pre_ping=True, pool_size=5, max_overflow=10)

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

# Async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Ensures the session is properly closed after the request completes.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """FastAPI dependency that extracts and validates the current user from JWT.

    Raises HTTPException 401 if token is missing or invalid.
    """
    from app.models.user import User

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录，请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = verify_access_token(credentials.credentials)
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse user ID from token
    try:
        parsed_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).where(User.id == parsed_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_family(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """FastAPI dependency that gets the current user's active family.

    For now, returns the first family the user belongs to.
    In demo mode, auto-creates a family if the user has none.
    """
    from app.models.family import Family, FamilyMember, FamilyRole

    stmt = select(FamilyMember).where(FamilyMember.user_id == current_user.id)
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if membership is None:
        # Auto-create a family for the user in demo mode
        if settings.DEBUG:
            import secrets
            family = Family(
                name=f"{current_user.nickname or 'Demo'}的家庭",
                invite_code=secrets.token_hex(6),
                created_by=current_user.id,
            )
            db.add(family)
            await db.flush()
            await db.refresh(family)

            membership = FamilyMember(
                family_id=family.id,
                user_id=current_user.id,
                role=FamilyRole.admin,
                nickname_in_family=current_user.nickname or "我",
            )
            db.add(membership)
            await db.flush()
            await db.refresh(membership)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您尚未加入任何家庭",
            )

    return membership
