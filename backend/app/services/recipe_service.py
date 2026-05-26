"""Recipe service layer — business logic for recipe CRUD."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import MemberFoodPreference, Recipe


async def get_recipes(
    db: AsyncSession,
    family_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Recipe], int]:
    """Get paginated list of recipes for a family.

    Args:
        db: Database session.
        family_id: Family UUID to filter by.
        page: Page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        Tuple of (recipes list, total count).
    """
    base_query = select(Recipe).where(Recipe.family_id == family_id)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results
    offset = (page - 1) * page_size
    query = base_query.order_by(Recipe.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    recipes = list(result.scalars().all())

    return recipes, total


async def get_recipe_by_id(
    db: AsyncSession,
    recipe_id: uuid.UUID,
    family_id: uuid.UUID,
) -> Recipe | None:
    """Get a single recipe by ID, scoped to a family.

    Args:
        db: Database session.
        recipe_id: Recipe UUID.
        family_id: Family UUID for access control.

    Returns:
        Recipe instance or None if not found.
    """
    query = select(Recipe).where(
        Recipe.id == recipe_id, Recipe.family_id == family_id
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_recipe(
    db: AsyncSession,
    family_id: uuid.UUID,
    created_by: uuid.UUID,
    name: str,
    description: str | None = None,
    ingredients: list | None = None,
    steps: list | None = None,
) -> Recipe:
    """Create a new recipe.

    Args:
        db: Database session.
        family_id: Family UUID.
        created_by: User UUID (recipe creator).
        name: Recipe name.
        description: Recipe description (optional).
        ingredients: List of ingredients (optional).
        steps: List of steps (optional).

    Returns:
        Created Recipe instance.
    """
    recipe = Recipe(
        family_id=family_id,
        created_by=created_by,
        name=name,
        description=description,
        ingredients=ingredients,
        steps=steps,
    )
    db.add(recipe)
    await db.flush()
    await db.refresh(recipe)
    return recipe


async def update_recipe(
    db: AsyncSession,
    recipe: Recipe,
    name: str | None = None,
    description: str | None = None,
    ingredients: list | None = None,
    steps: list | None = None,
) -> Recipe:
    """Update an existing recipe.

    Args:
        db: Database session.
        recipe: Recipe instance to update.
        name: New name (optional).
        description: New description (optional).
        ingredients: New ingredients list (optional).
        steps: New steps list (optional).

    Returns:
        Updated Recipe instance.
    """
    if name is not None:
        recipe.name = name
    if description is not None:
        recipe.description = description
    if ingredients is not None:
        recipe.ingredients = ingredients
    if steps is not None:
        recipe.steps = steps

    await db.flush()
    await db.refresh(recipe)
    return recipe


async def delete_recipe(db: AsyncSession, recipe: Recipe) -> None:
    """Delete a recipe.

    Args:
        db: Database session.
        recipe: Recipe instance to delete.
    """
    await db.delete(recipe)
    await db.flush()


# ─── Food Preferences (Task 17.2) ─────────────────────────────────────────────


async def get_food_preferences_summary(
    db: AsyncSession,
    family_id: uuid.UUID,
) -> list[MemberFoodPreference]:
    """Get all family members' food preferences.

    Args:
        db: Database session.
        family_id: Family UUID.

    Returns:
        List of MemberFoodPreference instances.
    """
    query = select(MemberFoodPreference).where(
        MemberFoodPreference.family_id == family_id
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_food_preference_by_user(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
) -> MemberFoodPreference | None:
    """Get a specific member's food preferences.

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID.

    Returns:
        MemberFoodPreference instance or None.
    """
    query = select(MemberFoodPreference).where(
        MemberFoodPreference.family_id == family_id,
        MemberFoodPreference.user_id == user_id,
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def upsert_food_preference(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
    taste_preferences: dict | None = None,
    favorite_foods: list | None = None,
    food_allergies: list | None = None,
    dietary_restrictions: list | None = None,
) -> MemberFoodPreference:
    """Create or update a member's food preferences.

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID.
        taste_preferences: Taste preferences dict.
        favorite_foods: Favorite foods list.
        food_allergies: Food allergies list.
        dietary_restrictions: Dietary restrictions list.

    Returns:
        Created or updated MemberFoodPreference instance.
    """
    pref = await get_food_preference_by_user(db, family_id, user_id)

    if pref is None:
        pref = MemberFoodPreference(
            family_id=family_id,
            user_id=user_id,
            taste_preferences=taste_preferences,
            favorite_foods=favorite_foods,
            food_allergies=food_allergies,
            dietary_restrictions=dietary_restrictions,
        )
        db.add(pref)
    else:
        if taste_preferences is not None:
            pref.taste_preferences = taste_preferences
        if favorite_foods is not None:
            pref.favorite_foods = favorite_foods
        if food_allergies is not None:
            pref.food_allergies = food_allergies
        if dietary_restrictions is not None:
            pref.dietary_restrictions = dietary_restrictions

    await db.flush()
    await db.refresh(pref)
    return pref


# ─── AI Recipe Generation (Task 19.2) ─────────────────────────────────────────


async def generate_recipe_content(
    db: AsyncSession,
    recipe: Recipe,
    dish_name: str,
) -> dict:
    """Generate recipe ingredients and steps using AI, then update the recipe.

    Args:
        db: Database session.
        recipe: Recipe instance to update.
        dish_name: Name of the dish to generate content for.

    Returns:
        Dict with generated ingredients, steps, and description.
    """
    result = await _ai_generate_recipe(db, dish_name)

    # Update the recipe with generated content
    if result.get("ingredients"):
        recipe.ingredients = result["ingredients"]
    if result.get("steps"):
        recipe.steps = result["steps"]
    if result.get("description"):
        recipe.description = result["description"]

    await db.flush()
    await db.refresh(recipe)
    return result


async def generate_recipe_content_preview(
    db: AsyncSession,
    dish_name: str,
) -> dict:
    """Generate recipe content preview without saving (for creation flow).

    Args:
        db: Database session.
        dish_name: Name of the dish to generate content for.

    Returns:
        Dict with generated ingredients, steps, and description.
    """
    return await _ai_generate_recipe(db, dish_name)


async def _ai_generate_recipe(db: AsyncSession, dish_name: str) -> dict:
    """Internal helper: call AI service to generate recipe content.

    Args:
        db: Database session (needed for AI config lookup).
        dish_name: Name of the dish.

    Returns:
        Dict with keys: ingredients (list), steps (list), description (str).
    """
    import json
    import logging

    logger = logging.getLogger(__name__)

    prompt = (
        f"请为菜品「{dish_name}」生成详细的食谱内容，包括食材清单和做法步骤。\n"
        f"请严格按照以下JSON格式返回：\n"
        f'{{"description": "一句话菜品描述", '
        f'"ingredients": ["食材1 用量", "食材2 用量", ...], '
        f'"steps": ["步骤1描述", "步骤2描述", ...]}}\n'
        f"要求：\n"
        f"- 食材清单包含具体用量\n"
        f"- 步骤描述清晰简洁\n"
        f"- 只返回JSON，不要其他内容"
    )

    try:
        from app.services.ai_service import ai_adapter

        generated_text = await ai_adapter.generate_text("text_generation", prompt, db)

        # Parse the AI response as JSON
        # Try to extract JSON from the response (AI might wrap it in markdown code blocks)
        text = generated_text.strip()
        if text.startswith("```"):
            # Remove markdown code block markers
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            text = text.strip()

        result = json.loads(text)
        return {
            "ingredients": result.get("ingredients", []),
            "steps": result.get("steps", []),
            "description": result.get("description", ""),
        }
    except Exception as e:
        logger.warning(f"AI recipe generation failed for '{dish_name}': {e}")
        # Return a sensible fallback
        return _get_fallback_recipe(dish_name)


def _get_fallback_recipe(dish_name: str) -> dict:
    """Generate a simple fallback recipe when AI is unavailable.

    Args:
        dish_name: Name of the dish.

    Returns:
        Dict with basic recipe structure.
    """
    return {
        "description": f"{dish_name} - 家常做法",
        "ingredients": [
            f"{dish_name}主料 适量",
            "盐 适量",
            "油 适量",
            "葱姜蒜 适量",
        ],
        "steps": [
            "准备食材，清洗干净",
            "将主料切好备用",
            "热锅凉油，爆香葱姜蒜",
            "加入主料翻炒",
            "调味，出锅装盘",
        ],
    }
