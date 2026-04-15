from datetime import date

from pydantic import BaseModel, ConfigDict

from backend.app.schemas.recipe import RecipeRead


class MealPlanItemCreate(BaseModel):
    plan_date: date
    meal_type: str = "jantar"
    notes: str | None = None
    recipe_id: int


class MealPlanItemRead(BaseModel):
    id: int
    plan_date: date
    meal_type: str
    notes: str | None = None
    recipe: RecipeRead

    model_config = ConfigDict(from_attributes=True)