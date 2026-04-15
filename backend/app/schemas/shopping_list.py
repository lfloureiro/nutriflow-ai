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