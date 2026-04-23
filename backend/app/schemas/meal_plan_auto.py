from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AutoMealPlanRequest(BaseModel):
    household_id: int
    start_date: date
    end_date: date
    meal_types: list[str] = Field(default_factory=lambda: ["almoco", "jantar"])
    skip_existing: bool = True


class AutoMealPlanSuggestionRead(BaseModel):
    plan_date: date
    meal_type: str
    action: str
    recipe_id: int | None = None
    recipe_name: str | None = None
    categoria_alimentar: str | None = None
    proteina_principal: str | None = None
    score: float | None = None
    heuristic_score: float | None = None
    ml_score: float | None = None
    final_score: float | None = None
    average_rating: float | None = None
    ratings_count: int = 0
    reasons: list[str] = Field(default_factory=list)
    engine_version: str | None = None


class AutoMealPlanPreviewRead(BaseModel):
    household_id: int
    start_date: date
    end_date: date
    meal_types: list[str]
    skip_existing: bool
    suggestions: list[AutoMealPlanSuggestionRead]


class AutoMealPlanApplyRead(BaseModel):
    household_id: int
    start_date: date
    end_date: date
    meal_types: list[str]
    skip_existing: bool
    created_count: int
    skipped_count: int
    suggestions: list[AutoMealPlanSuggestionRead]


class AutoMealPlanAdjustedSuggestionWrite(BaseModel):
    plan_date: date
    meal_type: str
    original_action: str
    original_recipe_id: int | None = None
    adjusted_recipe_id: int | None = None
    apply_decision: Literal["keep", "replace", "ignore", "skip_existing"] = "keep"
    score: float | None = None
    heuristic_score: float | None = None
    ml_score: float | None = None
    final_score: float | None = None
    average_rating: float | None = None
    ratings_count: int = 0
    reasons: list[str] = Field(default_factory=list)
    engine_version: str | None = None


class AutoMealPlanAdjustedRequest(BaseModel):
    household_id: int
    start_date: date
    end_date: date
    meal_types: list[str] = Field(default_factory=lambda: ["almoco", "jantar"])
    skip_existing: bool = True
    suggestions: list[AutoMealPlanAdjustedSuggestionWrite] = Field(default_factory=list)


class AutoMealPlanAdjustedApplyRead(BaseModel):
    household_id: int
    start_date: date
    end_date: date
    meal_types: list[str]
    skip_existing: bool
    created_count: int
    skipped_count: int
    ignored_count: int
    replaced_count: int
    suggestions: list[AutoMealPlanSuggestionRead]