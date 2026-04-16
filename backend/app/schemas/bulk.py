from datetime import date

from pydantic import BaseModel


class BulkIngredientImportItem(BaseModel):
    name: str


class BulkRecipeImportItem(BaseModel):
    name: str
    description: str | None = None


class BulkIngredientImportRequest(BaseModel):
    items: list[BulkIngredientImportItem]
    skip_existing: bool = True


class BulkRecipeImportRequest(BaseModel):
    items: list[BulkRecipeImportItem]
    skip_existing: bool = True


class BulkImportResult(BaseModel):
    total_received: int
    created: int
    skipped: int


class BulkMealPlanUpdateItem(BaseModel):
    id: int
    plan_date: date | None = None
    meal_type: str | None = None
    notes: str | None = None
    recipe_id: int | None = None


class BulkMealPlanUpdateRequest(BaseModel):
    items: list[BulkMealPlanUpdateItem]