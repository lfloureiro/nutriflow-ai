from datetime import date

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
    average_rating: float | None = None
    ratings_count: int = 0
    reasons: list[str] = Field(default_factory=list)


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