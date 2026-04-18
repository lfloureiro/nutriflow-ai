from pydantic import BaseModel, Field


class MealPlanItemCreateScoped(BaseModel):
    household_id: int
    plan_date: str
    meal_type: str = Field(..., min_length=1, max_length=50)
    notes: str | None = Field(default=None, max_length=500)
    recipe_id: int


class MealPlanItemUpdateScoped(BaseModel):
    household_id: int | None = None
    plan_date: str | None = None
    meal_type: str | None = Field(default=None, min_length=1, max_length=50)
    notes: str | None = Field(default=None, max_length=500)
    recipe_id: int | None = None