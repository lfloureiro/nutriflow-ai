from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.recipe_ingredient import RecipeIngredientRead


class RecipeCreate(BaseModel):
    name: str
    description: str | None = None
    categoria_alimentar: str | None = None
    proteina_principal: str | None = None
    adequado_refeicao: str | None = None
    auto_plan_enabled: bool = True


class RecipeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    categoria_alimentar: str | None = None
    proteina_principal: str | None = None
    adequado_refeicao: str | None = None
    auto_plan_enabled: bool | None = None


class RecipeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    categoria_alimentar: str | None = None
    proteina_principal: str | None = None
    adequado_refeicao: str | None = None
    auto_plan_enabled: bool


class RecipeDetail(RecipeRead):
    ingredient_links: list[RecipeIngredientRead] = Field(default_factory=list)