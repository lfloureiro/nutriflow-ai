from datetime import datetime

from pydantic import BaseModel


class ShoppingListSourceRead(BaseModel):
    recipe_id: int
    recipe_name: str
    plan_date: str
    meal_type: str


class ShoppingListItemRead(BaseModel):
    ingredient_id: int
    ingredient_name: str
    quantity: str | None = None
    unit: str | None = None
    sources: list[ShoppingListSourceRead]
    in_cart: bool = False


class ShoppingListItemStateUpsert(BaseModel):
    household_id: int
    ingredient_id: int
    unit: str | None = None
    in_cart: bool


class ShoppingListItemStateRead(BaseModel):
    household_id: int
    ingredient_id: int
    unit: str | None = None
    in_cart: bool
    updated_at: datetime