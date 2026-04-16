from datetime import date

from pydantic import BaseModel, ConfigDict

from backend.app.schemas.recipe import RecipeRead


class MealPlanItemCreate(BaseModel):
    plan_date: date
    meal_type: str = "jantar"
    notes: str | None = None
    recipe_id: int


class MealPlanItemUpdate(BaseModel):
    plan_date: date | None = None
    meal_type: str | None = None
    notes: str | None = None
    recipe_id: int | None = None


class MealPlanItemRead(BaseModel):
    id: int
    plan_date: date
    meal_type: str
    notes: str | None = None
    recipe: RecipeRead

    model_config = ConfigDict(from_attributes=True)


class NextMealSlotRead(BaseModel):
    plan_date: date
    meal_type: str