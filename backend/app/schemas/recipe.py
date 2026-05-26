"""Recipe-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ─── Request Schemas ───────────────────────────────────────────────────────────


class RecipeCreateRequest(BaseModel):
    """Request body for creating a recipe."""

    name: str = Field(..., min_length=1, max_length=128, description="菜品名称")
    description: str | None = Field(None, description="菜品描述")
    ingredients: list | None = Field(None, description="食材列表")
    steps: list | None = Field(None, description="步骤列表")


class RecipeUpdateRequest(BaseModel):
    """Request body for updating a recipe."""

    name: str | None = Field(None, min_length=1, max_length=128, description="菜品名称")
    description: str | None = Field(None, description="菜品描述")
    ingredients: list | None = Field(None, description="食材列表")
    steps: list | None = Field(None, description="步骤列表")


class RecipeGenerateRequest(BaseModel):
    """Request body for AI recipe content generation."""

    dish_name: str | None = Field(None, min_length=1, max_length=128, description="菜品名称（可选，默认使用食谱名称）")


# ─── Food Preference Schemas (Task 17.2) ──────────────────────────────────────


class FoodPreferenceUpdateRequest(BaseModel):
    """Request body for updating a member's food preferences."""

    taste_preferences: dict | None = Field(None, description="口味偏好（如辣度、甜度、酸度）")
    favorite_foods: list | None = Field(None, description="喜欢的食物列表")
    food_allergies: list | None = Field(None, description="食物过敏列表")
    dietary_restrictions: list | None = Field(None, description="饮食禁忌列表")


class FoodPreferenceResponse(BaseModel):
    """Response containing a member's food preferences."""

    id: uuid.UUID
    family_id: uuid.UUID
    user_id: uuid.UUID
    taste_preferences: dict | None = None
    favorite_foods: list | None = None
    food_allergies: list | None = None
    dietary_restrictions: list | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FoodPreferenceSummaryResponse(BaseModel):
    """Summary of all family members' food preferences."""

    items: list[FoodPreferenceResponse]
    total: int


# ─── Response Schemas ──────────────────────────────────────────────────────────


class RecipeResponse(BaseModel):
    """Response containing recipe information."""

    id: uuid.UUID
    family_id: uuid.UUID
    created_by: uuid.UUID
    name: str
    description: str | None = None
    cover_image_url: str | None = None
    display_text: str | None = None
    ingredients: list | None = None
    steps: list | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecipeListResponse(BaseModel):
    """Paginated list of recipes."""

    items: list[RecipeResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class RecipeGenerateResponse(BaseModel):
    """Response from AI recipe content generation."""

    id: uuid.UUID | None = None
    name: str
    ingredients: list = Field(default_factory=list, description="AI生成的食材清单")
    steps: list = Field(default_factory=list, description="AI生成的做法步骤")
    description: str | None = Field(None, description="AI生成的菜品描述")
