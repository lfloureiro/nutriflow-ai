from pydantic import BaseModel, ConfigDict

from backend.app.schemas.ingredient import IngredientRead


class RecipeIngredientCreate(BaseModel):
    ingredient_id: int
    quantity: str | None = None
    unit: str | None = None


class RecipeIngredientRead(BaseModel):
    id: int
    quantity: str | None = None
    unit: str | None = None
    ingredient: IngredientRead

    model_config = ConfigDict(from_attributes=True)