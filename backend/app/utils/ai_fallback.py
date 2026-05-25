"""AI generation fallback utilities.

When AI generation fails (all providers exhausted), these utilities provide
graceful degradation by using default placeholder images and original text.
"""

import logging

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wish import Wish
from app.models.goal import Goal
from app.models.plan import Plan
from app.models.task import Task
from app.models.action import Action

logger = logging.getLogger(__name__)

# Default placeholder image shown when AI image generation fails
DEFAULT_PLACEHOLDER_IMAGE_URL = (
    "https://img.alicdn.com/imgextra/i4/O1CN01Z5paLz1O0zuCC7osS_!!6000000001644-55-tps-83-82.svg"
)

# Mapping of entity types to their SQLAlchemy model classes
_ENTITY_MODEL_MAP: dict[str, type] = {
    "wish": Wish,
    "goal": Goal,
    "plan": Plan,
    "task": Task,
    "action": Action,
}


def get_fallback_text(original_text: str) -> str:
    """Return the original text as-is when AI text enhancement fails.

    Args:
        original_text: The user's original input text.

    Returns:
        The original text unchanged.
    """
    return original_text


def get_fallback_image() -> str:
    """Return the default placeholder image URL when AI image generation fails.

    Returns:
        The URL of the default placeholder image.
    """
    return DEFAULT_PLACEHOLDER_IMAGE_URL


def get_fallback_vision_story(title: str) -> str:
    """Return a default vision story when AI vision story generation fails.

    Uses the original wish title to construct a meaningful fallback message.

    Args:
        title: The original wish title.

    Returns:
        A fallback vision story string incorporating the title.
    """
    return f"愿望：{title}"


async def handle_ai_generation_failure(
    entity_type: str,
    entity_id: str,
    field: str,
    fallback_value: str,
    db_session: AsyncSession,
) -> None:
    """Update an entity with a fallback value when AI generation fails.

    This function is called when all AI providers have been exhausted and
    generation has ultimately failed. It updates the specified field of the
    entity with the provided fallback value (either placeholder image URL
    or original text).

    Args:
        entity_type: The type of entity (e.g., "wish", "goal", "plan", "task", "action").
        entity_id: The UUID of the entity to update.
        field: The field name to update (e.g., "cover_image_url", "display_text").
        fallback_value: The fallback value to set on the field.
        db_session: The async database session.

    Raises:
        ValueError: If the entity_type is not recognized.
    """
    model_class = _ENTITY_MODEL_MAP.get(entity_type)
    if model_class is None:
        raise ValueError(
            f"Unknown entity type: '{entity_type}'. "
            f"Supported types: {list(_ENTITY_MODEL_MAP.keys())}"
        )

    logger.warning(
        "AI generation failed for %s(%s).%s — applying fallback value",
        entity_type,
        entity_id,
        field,
    )

    stmt = (
        update(model_class)
        .where(model_class.id == entity_id)
        .values({field: fallback_value})
    )
    await db_session.execute(stmt)
    await db_session.commit()
