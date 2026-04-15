from pydantic import BaseModel, ConfigDict

from backend.app.schemas.recipe_ingredient import RecipeIngredientRead


class RecipeCreate(BaseModel):
    name: str
    description: str | None = None


class RecipeRead(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RecipeDetail(RecipeRead):
    ingredient_links: list[RecipeIngredientRead] = []