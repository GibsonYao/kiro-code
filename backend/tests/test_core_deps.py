"""Tests for core/deps.py - async engine and session management."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import async_session_factory, engine, get_db


def test_engine_is_configured():
    """Engine should be configured with the asyncpg driver."""
    assert engine is not None
    assert "asyncpg" in str(engine.url)


def test_engine_pool_settings():
    """Engine should have pool_size=5 and max_overflow=10."""
    pool = engine.pool
    assert pool.size() == 5
    assert pool._max_overflow == 10


def test_session_factory_is_configured():
    """Session factory should produce AsyncSession instances."""
    assert async_session_factory is not None
    assert async_session_factory.class_ is AsyncSession


@pytest.mark.asyncio
async def test_get_db_yields_async_session():
    """get_db should yield an AsyncSession and close it after use."""
    gen = get_db()
    session = await gen.__anext__()
    assert isinstance(session, AsyncSession)
    # Cleanup - simulate end of request
    try:
        await gen.__anext__()
    except StopAsyncIteration:
        pass
