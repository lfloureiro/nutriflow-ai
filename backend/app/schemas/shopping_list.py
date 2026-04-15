from pydantic import BaseModel


class ShoppingListItemRead(BaseModel):
    ingredient_id: int
    ingredient_name: str
    quantity: str | None = None
    unit: str | None = None
    recipe_id: int
    recipe_name: str
    plan_date: str
    meal_type: str