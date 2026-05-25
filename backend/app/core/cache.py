"""Redis cache utilities for AI configuration caching.

Provides a Redis client singleton and helper functions for caching
active AI model configurations with a 5-minute TTL.
"""

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis client singleton
_redis_client: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    """Get or create the Redis client singleton.

    Returns:
        An async Redis client instance.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_client


async def get_cached(key: str) -> dict | list | None:
    """Get a cached value by key.

    Args:
        key: The cache key to look up.

    Returns:
        Deserialized cached value, or None if not found or on error.
    """
    try:
        client = await get_redis_client()
        value = await client.get(key)
        if value is not None:
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Cache get failed for key={key}: {e}")
    return None


async def set_cached(key: str, value: Any, ttl: int = 300) -> None:
    """Set a value in cache with TTL.

    Args:
        key: The cache key.
        value: The value to cache (must be JSON-serializable).
        ttl: Time-to-live in seconds (default: 300 = 5 minutes).
    """
    try:
        client = await get_redis_client()
        await client.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        logger.warning(f"Cache set failed for key={key}: {e}")


async def invalidate_cache(key_pattern: str) -> None:
    """Invalidate cache entries matching a pattern.

    Uses SCAN to find and delete keys matching the pattern.

    Args:
        key_pattern: A glob-style pattern (e.g., "ai_config:*").
    """
    try:
        client = await get_redis_client()
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor=cursor, match=key_pattern, count=100)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break
    except Exception as e:
        logger.warning(f"Cache invalidation failed for pattern={key_pattern}: {e}")


async def invalidate_ai_config_cache(config_key: str) -> None:
    """Invalidate cached AI config for a specific config_key.

    Should be called when admin updates AI model configurations.

    Args:
        config_key: The config key to invalidate (e.g., 'text_generation').
    """
    cache_key = f"ai_config:{config_key}"
    try:
        client = await get_redis_client()
        await client.delete(cache_key)
        logger.info(f"Invalidated AI config cache for key={config_key}")
    except Exception as e:
        logger.warning(f"Failed to invalidate AI config cache for key={config_key}: {e}")
