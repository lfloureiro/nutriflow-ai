from datetime import date
from typing import Literal

from pydantic import BaseModel


class BulkIngredientImportItem(BaseModel):
    name: str


class BulkRecipeImportItem(BaseModel):
    name: str
    description: str | None = None


class BulkHouseholdImportItem(BaseModel):
    name: str


class BulkFamilyMemberImportItem(BaseModel):
    household_id: int
    name: str


class BulkRecipeIngredientImportItem(BaseModel):
    recipe_id: int
    ingredient_id: int
    quantity: str | None = None
    unit: str | None = None


class BulkMealPlanImportItem(BaseModel):
    plan_date: date
    meal_type: str
    notes: str | None = None
    recipe_id: int


class BulkFeedbackImportItem(BaseModel):
    meal_plan_item_id: int
    family_member_id: int
    reaction: Literal["gostou", "neutro", "nao_gostou"]
    note: str | None = None


class BulkIngredientImportRequest(BaseModel):
    items: list[BulkIngredientImportItem]
    skip_existing: bool = True


class BulkRecipeImportRequest(BaseModel):
    items: list[BulkRecipeImportItem]
    skip_existing: bool = True


class BulkHouseholdImportRequest(BaseModel):
    items: list[BulkHouseholdImportItem]
    skip_existing: bool = True


class BulkFamilyMemberImportRequest(BaseModel):
    items: list[BulkFamilyMemberImportItem]
    skip_existing: bool = True


class BulkRecipeIngredientImportRequest(BaseModel):
    items: list[BulkRecipeIngredientImportItem]
    skip_existing: bool = True


class BulkMealPlanImportRequest(BaseModel):
    items: list[BulkMealPlanImportItem]
    skip_existing: bool = True


class BulkFeedbackImportRequest(BaseModel):
    items: list[BulkFeedbackImportItem]
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


class BulkDeleteRequest(BaseModel):
    ids: list[int]


class BulkDeleteResult(BaseModel):
    requested: int
    deleted: int