"""Recipe API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_family, get_current_user, get_db
from app.models.family import FamilyMember
from app.models.user import User
from app.schemas.recipe import (
    FoodPreferenceResponse,
    FoodPreferenceSummaryResponse,
    FoodPreferenceUpdateRequest,
    RecipeCreateRequest,
    RecipeGenerateRequest,
    RecipeGenerateResponse,
    RecipeListResponse,
    RecipeResponse,
    RecipeUpdateRequest,
)
from app.services.recipe_service import (
    create_recipe,
    delete_recipe,
    generate_recipe_content,
    get_food_preferences_summary,
    get_recipe_by_id,
    get_recipes,
    update_recipe,
    upsert_food_preference,
)

router = APIRouter()


@router.get("/", response_model=RecipeListResponse)
async def list_recipes(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of recipes for the current family."""
    recipes, total = await get_recipes(
        db=db,
        family_id=membership.family_id,
        page=page,
        page_size=page_size,
    )

    return RecipeListResponse(
        items=[RecipeResponse.model_validate(r) for r in recipes],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("/", response_model=RecipeResponse, status_code=status.HTTP_201_CREATED)
async def create_recipe_endpoint(
    body: RecipeCreateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Create a new recipe."""
    recipe = await create_recipe(
        db=db,
        family_id=membership.family_id,
        created_by=current_user.id,
        name=body.name,
        description=body.description,
        ingredients=body.ingredients,
        steps=body.steps,
    )

    return RecipeResponse.model_validate(recipe)


# ─── AI Recipe Generation Preview (Task 19.2) ─────────────────────────────────
# NOTE: This route MUST be defined before /{recipe_id} to avoid path conflicts


@router.post("/generate-preview", response_model=RecipeGenerateResponse)
async def generate_recipe_preview(
    body: RecipeGenerateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """AI-generate recipe content preview without saving (for creation flow).

    Generates ingredients and steps based on dish name before creating the recipe.
    """
    if not body.dish_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="菜品名称不能为空",
        )

    from app.services.recipe_service import generate_recipe_content_preview

    result = await generate_recipe_content_preview(db=db, dish_name=body.dish_name)

    return RecipeGenerateResponse(
        id=None,
        name=body.dish_name,
        ingredients=result.get("ingredients", []),
        steps=result.get("steps", []),
        description=result.get("description"),
    )


# ─── Food Preferences Endpoints (Task 19.3) ───────────────────────────────────
# NOTE: These routes MUST be defined before /{recipe_id} to avoid path conflicts


@router.get("/preferences", response_model=FoodPreferenceSummaryResponse)
async def get_preferences_summary(
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get all family members' food preferences summary."""
    prefs = await get_food_preferences_summary(db=db, family_id=membership.family_id)

    return FoodPreferenceSummaryResponse(
        items=[FoodPreferenceResponse.model_validate(p) for p in prefs],
        total=len(prefs),
    )


@router.put("/preferences/{user_id}", response_model=FoodPreferenceResponse)
async def update_preferences(
    user_id: uuid.UUID,
    body: FoodPreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Update a family member's food preferences.

    Only the member themselves or a family admin can update preferences.
    """
    # Permission check: only self or admin
    if user_id != current_user.id and membership.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能修改自己的饮食偏好，或由家庭管理员修改",
        )

    pref = await upsert_food_preference(
        db=db,
        family_id=membership.family_id,
        user_id=user_id,
        taste_preferences=body.taste_preferences,
        favorite_foods=body.favorite_foods,
        food_allergies=body.food_allergies,
        dietary_restrictions=body.dietary_restrictions,
    )

    return FoodPreferenceResponse.model_validate(pref)


# ─── Recipe by ID Endpoints ───────────────────────────────────────────────────


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get a single recipe by ID."""
    recipe = await get_recipe_by_id(db=db, recipe_id=recipe_id, family_id=membership.family_id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="食谱不存在",
        )
    return RecipeResponse.model_validate(recipe)


@router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe_endpoint(
    recipe_id: uuid.UUID,
    body: RecipeUpdateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Update a recipe. Only the creator or family admin can update."""
    recipe = await get_recipe_by_id(db=db, recipe_id=recipe_id, family_id=membership.family_id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="食谱不存在",
        )

    # Only the recipe creator or family admin can update
    if recipe.created_by != current_user.id and membership.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有食谱创建者或家庭管理员可以修改食谱",
        )

    recipe = await update_recipe(
        db=db,
        recipe=recipe,
        name=body.name,
        description=body.description,
        ingredients=body.ingredients,
        steps=body.steps,
    )

    return RecipeResponse.model_validate(recipe)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe_endpoint(
    recipe_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Delete a recipe. Only the creator or family admin can delete."""
    recipe = await get_recipe_by_id(db=db, recipe_id=recipe_id, family_id=membership.family_id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="食谱不存在",
        )

    # Only the recipe creator or family admin can delete
    if recipe.created_by != current_user.id and membership.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有食谱创建者或家庭管理员可以删除食谱",
        )

    await delete_recipe(db=db, recipe=recipe)


# ─── AI Recipe Generation for Existing Recipe (Task 19.2) ─────────────────────


@router.post("/{recipe_id}/generate", response_model=RecipeGenerateResponse)
async def generate_recipe_content_endpoint(
    recipe_id: uuid.UUID,
    body: RecipeGenerateRequest | None = None,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """AI-generate ingredients and steps for a recipe based on its name.

    Optionally accepts a dish_name override; otherwise uses the recipe's existing name.
    """
    recipe = await get_recipe_by_id(db=db, recipe_id=recipe_id, family_id=membership.family_id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="食谱不存在",
        )

    dish_name = body.dish_name if body and body.dish_name else recipe.name
    result = await generate_recipe_content(db=db, recipe=recipe, dish_name=dish_name)

    return RecipeGenerateResponse(
        id=recipe.id,
        name=recipe.name,
        ingredients=result.get("ingredients", []),
        steps=result.get("steps", []),
        description=result.get("description"),
    )
